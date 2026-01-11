import { useState, useEffect } from 'react';

type DocumentRow = {
    doc_id: string;
    filename: string | null;
    status: "processing" | "ready" | "failed";
    page_count: number | null;
    created_at: string;
    updated_at: string;
  };

const DocumentsPanel = () => {
    const [documents, setDocuments] = useState<DocumentRow[]>([]);

    async function getDocuments() {
        const response = await fetch("http://localhost:8000/documents", {
            method: "GET"
        });
        const docs: DocumentRow[] = await response.json();
        setDocuments(docs);
    }

    useEffect(() => {
        getDocuments();
        const id = setInterval(getDocuments, 1500);
        return () => clearInterval(id);
    }, []);

    async function deleteDocument(docId: string) {
        const response = await fetch(`http://localhost:8000/documents/${docId}`, {
            method: "DELETE"
        });
        if (!response.ok) {
            const msg = await response.text().catch(() => "");
            console.error("delete failed", response.status, msg);
            return;
        }

        await getDocuments();
    }
    return (
        <div>
            {documents?.map((d) => (
            <div key={d.doc_id}>
                {d.filename} — {d.status}
                <button onClick={() => deleteDocument(d.doc_id)}>X</button>
            </div>
            
            ))}
        </div>
    );
}

export default DocumentsPanel;