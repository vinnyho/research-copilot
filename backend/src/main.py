import os
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
from pathlib import Path
import ingest_pdf
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_root():
    return {"ok": True}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/upload")
def uploadFile(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    print("Uploading file")
    doc_uuid = uuid.uuid4()
    doc_id = str(doc_uuid)

    Path("storage").mkdir(parents=True, exist_ok=True)
    pdf_path = Path("storage") / f"{doc_id}.pdf"

    with pdf_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (doc_id, filename, status, updated_at)
                VALUES (%s, %s, 'processing', now())
                ON CONFLICT (doc_id) DO UPDATE
                SET filename = EXCLUDED.filename, status = 'processing', error = NULL, updated_at = now()
                """,
                (doc_uuid, file.filename),
            )
        conn.commit()

    print("Background task")
    background_tasks.add_task(ingest_pdf.ingest_pdf, doc_id, str(pdf_path))

    return {"ok": True, "doc_id": doc_id}


@app.get("/search")
def search(query: str):
    ingest_pdf.search_query(query)
    return {"ok": True}


@app.get("/documents")
def docs():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT doc_id, filename, status, error, page_count, created_at, updated_at
                FROM documents
                ORDER BY updated_at DESC
                """
            )
            documents = cur.fetchall()

    return documents
