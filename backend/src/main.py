import os
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
from pathlib import Path
import ingest_pdf
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174" ],
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
    results = ingest_pdf.search_query(query)
    return results


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    doc_ids: list[str] | None = None
    limit: int = 8


@app.post("/chat")
def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    return ingest_pdf.answer_query(
        req.message,
        history=history,
        doc_ids=req.doc_ids,
        limit=req.limit
    )


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


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid doc_id (expected UUID)")


    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE doc_id = %s RETURNING doc_id", (doc_uuid,))
            deleted = cur.fetchone()
        conn.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        (Path("storage") / f"{doc_id}.pdf").unlink()
    except FileNotFoundError:
        pass

    return {"ok": True, "doc_id": doc_id}

