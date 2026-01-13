import { useState, useEffect } from 'react';

type DocumentRow = {
    doc_id: string;
    filename: string | null;
    status: "processing" | "ready" | "failed";
    page_count: number | null;
    created_at: string;
    updated_at: string;
  };

type Props = {
    selectedDocId: string | null;
    onSelectDoc: (docId: string) => void;
}

const DocumentsPanel = ({ selectedDocId, onSelectDoc }: Props) => {
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

    function yearFromIso(iso: string) {
        const d = new Date(iso);
        return Number.isFinite(d.getTime()) ? String(d.getFullYear()) : "";
    }

    return (
        <div className="docList">
            {documents?.map((d) => (
            <div
                key={d.doc_id}
                className={`docItem ${selectedDocId === d.doc_id ? "selected" : ""}`}
                onClick={() => onSelectDoc(d.doc_id)}
                role="button"
                tabIndex={0}
            >
                <div className="docIcon">📄</div>
                <div className="docMeta">
                    <div className="docTitle">{d.filename ?? "(untitled)"}</div>
                    <div className="docSub">
                        <span>{yearFromIso(d.created_at)}</span>
                        {d.page_count != null ? <span> · {d.page_count} pages</span> : null}
                    </div>
                    <div className="docStatusRow">
                        <span className={`statusPill ${d.status}`}>
                            {d.status === "ready" ? "Processed" : d.status === "processing" ? "Processing…" : "Failed"}
                        </span>
                    </div>
                </div>

                <button
                    className="iconBtn danger"
                    title="Delete"
                    onClick={(e) => {
                        e.stopPropagation();
                        deleteDocument(d.doc_id);
                    }}
                >
                    ×
                </button>
            </div>
            ))}
        </div>
    );
}

export default DocumentsPanel;