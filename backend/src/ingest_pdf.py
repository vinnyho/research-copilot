
from openai import OpenAI
import psycopg
import fitz
import os
import uuid
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from pgvector.psycopg import Vector
from psycopg.rows import dict_row

load_dotenv()

def ingest_pdf(doc_id, file_path):
    print("Ingesting PDF")
    
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

            doc_uuid = uuid.UUID(str(doc_id))


            cur.execute(
                """
                INSERT INTO documents (doc_id, status, updated_at)
                VALUES (%s, 'processing', now())
                ON CONFLICT (doc_id) DO UPDATE
                SET status = 'processing', error = NULL, updated_at = now()
                """,
                (doc_uuid,),
            )
            conn.commit()

            doc = fitz.open(file_path)
            page_count = doc.page_count
            chunk_index = 1
            for page_num, page in enumerate(doc, start=1):
                text = (page.get_text("text") or "").strip()

                if not text:
                    print(f"page {page_num}: (no text)")
                    continue

                text_for_embedding = text[:8000]

                resp = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text_for_embedding,
                )
                embedding = resp.data[0].embedding

                print(f"page {page_num}: embedded dims={len(embedding)} preview={text_for_embedding[:120]!r}")
                
                cur.execute(
                    """
                    INSERT INTO document_chunks (doc_id, page, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                    (doc_uuid, page_num, chunk_index, text_for_embedding, Vector(embedding)),
                )
                chunk_index += 1

            cur.execute(
                """
                UPDATE documents
                SET status = 'ready', page_count = %s, updated_at = now()
                WHERE doc_id = %s
                """,
                (page_count, doc_uuid),
            )
            conn.commit()

                        

def search_query(query: str, doc_ids: list[str] | None = None, limit: int = 5):

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.embeddings.create(model="text-embedding-3-small", input=query)
    query_embedding = resp.data[0].embedding

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        with conn.cursor(row_factory=dict_row) as cur:
            if doc_ids and len(doc_ids) > 0:
                doc_uuids = [uuid.UUID(d) for d in doc_ids]
                cur.execute(
                    """
                    SELECT dc.doc_id, dc.page, dc.chunk_index, dc.content, d.filename
                    FROM document_chunks dc
                    JOIN documents d ON dc.doc_id = d.doc_id
                    WHERE dc.doc_id = ANY(%s)
                    ORDER BY dc.embedding <-> %s
                    LIMIT %s
                    """,
                    (doc_uuids, Vector(query_embedding), limit),
                )
            else:
                cur.execute(
                    """
                    SELECT dc.doc_id, dc.page, dc.chunk_index, dc.content, d.filename
                    FROM document_chunks dc
                    JOIN documents d ON dc.doc_id = d.doc_id
                    ORDER BY dc.embedding <-> %s
                    LIMIT %s
                    """,
                    (Vector(query_embedding), limit),
                )
            return cur.fetchall()


def answer_query(
    message: str,
    history: list[dict] | None = None,
    doc_ids: list[str] | None = None,
    limit: int = 8
):
    chunks = search_query(message, doc_ids=doc_ids, limit=limit)

    sources = []
    for c in chunks:
        sources.append(
            f"[{c['filename']} | page {c['page']}]\n{c['content']}"
        )
    context = "\n\n".join(sources)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a research assistant. Answer ONLY using the provided sources. "
                "If the sources do not contain enough information, say you don't know. "
                "Cite sources inline like [filename | page X]. "
                "Keep responses concise and well-structured."
            ),
        },
    ]

    if history:
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({
        "role": "user",
        "content": f"Question:\n{message}\n\nSources:\n{context}",
    })

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    answer = resp.choices[0].message.content or ""
    citations = [
        {
            "doc_id": str(c["doc_id"]),
            "filename": c["filename"],
            "page": c["page"],
            "chunk_index": c["chunk_index"],
            "content": c["content"],
        }
        for c in chunks
    ]
    return {"answer": answer, "citations": citations}
