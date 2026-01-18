
from openai import OpenAI
import psycopg
import fitz
import os
import uuid
import json
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from pgvector.psycopg import Vector
from psycopg.rows import dict_row

load_dotenv()

CLAIM_EXTRACTION_PROMPT = """Extract key claims from this research paper page. A claim is a specific assertion, finding, result, or conclusion.

Categories:
- finding: A research result or discovery (e.g., "Model X achieves 95% accuracy")
- method: A methodological contribution (e.g., "We propose a novel attention mechanism")
- limitation: An acknowledged limitation (e.g., "Our approach struggles with long sequences")
- background: Important background facts cited (e.g., "Transformers have become the dominant architecture")

Return a JSON array of claims. Only include clear, specific claims. If no claims found, return empty array [].

Format:
[{"claim": "...", "category": "finding|method|limitation|background", "quote": "brief relevant quote from text"}]

Text:
"""


def extract_claims(client: OpenAI, text: str) -> list[dict]:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": CLAIM_EXTRACTION_PROMPT + text[:6000]}
            ],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "[]"
        data = json.loads(content)
        if isinstance(data, dict) and "claims" in data:
            return data["claims"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"Claim extraction error: {e}")
        return []


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

                claims = extract_claims(client, text_for_embedding)
                for claim in claims:
                    claim_text = claim.get("claim", "")
                    category = claim.get("category", "finding")
                    if category not in ("finding", "method", "limitation", "background"):
                        category = "finding"
                    source_quote = claim.get("quote", "")
                    if claim_text:
                        cur.execute(
                            """
                            INSERT INTO claims (doc_id, page, claim_text, category, source_quote)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (doc_uuid, page_num, claim_text, category, source_quote),
                        )
                print(f"page {page_num}: extracted {len(claims)} claims")

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


def generate_eval_questions(client: OpenAI, content: str, num_questions: int = 2) -> list[str]:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""Generate {num_questions} specific questions that can ONLY be answered using this text.
The questions should require information unique to this passage.

Return as JSON array of strings: ["question1", "question2"]

Text:
{content[:4000]}"""
                }
            ],
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        if isinstance(data, dict) and "questions" in data:
            return data["questions"][:num_questions]
        if isinstance(data, list):
            return data[:num_questions]
        return []
    except Exception as e:
        print(f"Question generation error: {e}")
        return []


def run_evaluation(k_values: list[int] = [3, 5, 10]) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT dc.doc_id, dc.page, dc.content, d.filename
                FROM document_chunks dc
                JOIN documents d ON dc.doc_id = d.doc_id
                WHERE d.status = 'ready'
                ORDER BY d.filename, dc.page
            """)
            chunks = cur.fetchall()

    if not chunks:
        return {"error": "No documents found"}

    eval_data = []
    print(f"Generating questions for {len(chunks)} chunks...")

    for chunk in chunks:
        questions = generate_eval_questions(client, chunk["content"], num_questions=2)
        for q in questions:
            eval_data.append({
                "question": q,
                "expected_doc_id": str(chunk["doc_id"]),
                "expected_page": chunk["page"],
                "filename": chunk["filename"]
            })
        print(f"  {chunk['filename']} p{chunk['page']}: {len(questions)} questions")

    print(f"\nRunning {len(eval_data)} evaluation queries...")

    results = {f"recall@{k}": 0 for k in k_values}
    hits = {k: 0 for k in k_values}

    for i, item in enumerate(eval_data):
        search_results = search_query(item["question"], limit=max(k_values))

        retrieved_pages = [
            (str(r["doc_id"]), r["page"]) for r in search_results
        ]

        expected = (item["expected_doc_id"], item["expected_page"])

        for k in k_values:
            if expected in retrieved_pages[:k]:
                hits[k] += 1

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(eval_data)} queries")

    total = len(eval_data)
    for k in k_values:
        results[f"recall@{k}"] = round(hits[k] / total * 100, 1) if total > 0 else 0

    results["total_queries"] = total
    results["total_documents"] = len(set(c["doc_id"] for c in chunks))
    results["total_pages"] = len(chunks)

    return results


def get_claims(doc_id: str | None = None):
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if doc_id:
                doc_uuid = uuid.UUID(doc_id)
                cur.execute(
                    """
                    SELECT c.id, c.doc_id, c.page, c.claim_text, c.category, c.source_quote, d.filename
                    FROM claims c
                    JOIN documents d ON c.doc_id = d.doc_id
                    WHERE c.doc_id = %s
                    ORDER BY c.page, c.id
                    """,
                    (doc_uuid,),
                )
            else:
                cur.execute(
                    """
                    SELECT c.id, c.doc_id, c.page, c.claim_text, c.category, c.source_quote, d.filename
                    FROM claims c
                    JOIN documents d ON c.doc_id = d.doc_id
                    ORDER BY d.filename, c.page, c.id
                    """
                )
            return cur.fetchall()
