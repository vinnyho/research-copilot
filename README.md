# AI Research Copilot

A full-stack research assistant for grounded Q&A over academic PDFs using Retrieval-Augmented Generation (RAG).
![alt text](image-1.png)
## Features

- **PDF Ingestion**: Upload PDFs with automatic text extraction and vector embedding
- **Semantic Search**: Query documents using natural language with pgvector similarity search
- **Q&A**: AI-powered chat with page-level citations linking to source documents
- **Claim Extraction**: Automatically extracts key findings, methods, and limitations from papers
- **PDF Viewer**: View source documents with direct navigation from citations
- **Conversation Memory**: Follow-up questions maintain context from previous messages
- **Document Filtering**: Select specific papers to search within

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite
- **Backend**: Python, FastAPI
- **Database**: PostgreSQL/pgvector extension
- **AI**: OpenAI API
- **Infrastructure**: Docker

## Architecture

```
User Query
    |
    v
[React Frontend] --> [FastAPI Backend] --> [OpenAI Embeddings]
                            |
                            v
                    [pgvector Search]
                            |
                            v
                    [Top-k Chunks Retrieved]
                            |
                            v
                    [GPT-4o-mini + Context] --> Response with Citations
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for PostgreSQL)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vinnyho/research-copilot.git
cd research
```

2. Start PostgreSQL with pgvector:
```bash
docker-compose up -d
```

3. Set up the backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Create `.env` file in `backend/`:
```
DATABASE_URL=postgresql://research:research@localhost:5433/research
OPENAI_API_KEY=your-api-key
```

5. Initialize the database:
```bash
psql postgresql://research:research@localhost:5433/research -f src/schema.sql
```

6. Start the backend:
```bash
cd src
uvicorn main:app --reload
```

7. Set up the frontend:
```bash
cd frontend
npm install
npm run dev
```

8. Open http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /upload | Upload a PDF document |
| GET | /documents | List all documents |
| DELETE | /documents/{id} | Delete a document |
| GET | /documents/{id}/pdf | Serve PDF file |
| POST | /chat | Send a message with RAG |
| GET | /search | Semantic search |
| GET | /claims | Get extracted claims |

## Tech Stack
Contributions are welcomed
