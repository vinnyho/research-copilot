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

    useEffect(() => {

        
        async function getDocuments(){
            const response = await fetch("http://localhost:8000/documents", {
                method: "GET"
            });
            console.log("test", response);
            const docs: DocumentRow[] = await response.json();
            setDocuments(docs);

        }
        getDocuments();
        const id = setInterval(getDocuments, 1500);
        return () => clearInterval(id);

    }, []);


    return (
        <div>
            {documents?.map((d) => (
            <div key={d.doc_id}>
                {d.filename} — {d.status}
            </div>
            ))}
        </div>
    );
}

export default DocumentsPanel;