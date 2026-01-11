CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS documents (
    doc_id uuid PRIMARY KEY,
    filename text,
    status text NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'failed')),
    error text,
    page_count int,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id bigserial PRIMARY KEY,
    doc_id uuid NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    page int NOT NULL,
    chunk_index int NOT NULL,
    content text NOT NULL,
    embedding vector(1536) NOT NULL,
    UNIQUE (doc_id, page, chunk_index)
);

CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS documents (
    doc_id uuid PRIMARY KEY,
    filename text,
    status text NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'failed')),
    error text,
    page_count int,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id bigserial PRIMARY KEY,
    doc_id uuid NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    page int NOT NULL,
    chunk_index int NOT NULL,
    content text NOT NULL,
    embedding vector(1536) NOT NULL,
    UNIQUE (doc_id, page, chunk_index)
);
