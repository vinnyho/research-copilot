import UploadPaper from '../features/uploadPaper'
import './App.css'
import DocumentsPanel from '../features/DocumentsPanel'
import { Workspace } from '../features'
import { useState, useEffect, useCallback } from 'react'

export type DocumentRow = {
  doc_id: string
  filename: string | null
  status: 'processing' | 'ready' | 'failed'
  page_count: number | null
  created_at: string
  updated_at: string
}

function App() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [documents, setDocuments] = useState<DocumentRow[]>([])

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/documents')
      const docs: DocumentRow[] = await res.json()
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to fetch documents:', err)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
    const id = setInterval(fetchDocuments, 1500)
    return () => clearInterval(id)
  }, [fetchDocuments])

  return (
    <div className="appLayout">
      <aside className="sidebar">
        <div className="sidebarHeader">
          <div className="sidebarTitleRow">
            <div className="sidebarTitle">Documents</div>
            <button className="iconBtn" title="Add">
              +
            </button>
          </div>
          <UploadPaper onUploadComplete={fetchDocuments} />
        </div>

        <div className="sidebarList">
          <DocumentsPanel
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={setSelectedDocId}
            onDelete={fetchDocuments}
          />
        </div>
      </aside>

      <main className="workspace">
        <Workspace documents={documents} />
      </main>
    </div>
  )
}

export default App
