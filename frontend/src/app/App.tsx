import UploadPaper from '../features/uploadPaper'
import './App.css'
import DocumentsPanel from '../features/DocumentsPanel'
import { Workspace } from '../features'
import { useState } from 'react'

function App() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)

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
          <UploadPaper />
        </div>

        <div className="sidebarList">
          <DocumentsPanel selectedDocId={selectedDocId} onSelectDoc={setSelectedDocId} />
        </div>
      </aside>

      <main className="workspace">
        <Workspace selectedDocId={selectedDocId} />
      </main>
    </div>
  )
}

export default App
