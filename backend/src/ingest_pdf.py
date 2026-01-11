
from openai import OpenAI
import psycopg
import fitz
import os
import uuid
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from pgvector.psycopg import Vector

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

                print(
                    f"page {page_num}: embedded dims={len(embedding)} preview={text_for_embedding[:120]!r}"
                )

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


def search_query(query):
    client = OpenAI()
    resp = client.embeddings.create(model="text-embedding-3-small", input=query)
    query_embedding = resp.data[0].embedding
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT doc_id, page, chunk_index, content
                FROM document_chunks
                ORDER BY embedding <-> %s
                LIMIT 5
                """,
                (Vector(query_embedding),),
            )
            rows = cur.fetchall()
            for i in rows:
                print(i)


from openai import OpenAI
import psycopg
import fitz
import os
import uuid
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from pgvector.psycopg import Vector

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

                        

def search_query(query):
    client = OpenAI()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = resp.data[0].embedding
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT doc_id, page, chunk_index, content
                FROM document_chunks
                ORDER BY embedding <-> %s
                LIMIT 5
                """,
                (Vector(query_embedding),),
            )
            rows = cur.fetchall()
            for i in rows:
                print(i)
