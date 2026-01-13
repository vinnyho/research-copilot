import { useMemo, useState } from 'react'

type TabId = 'chat' | 'claims' | 'pdf'

type Props = {
  selectedDocId: string | null
}

export default function Workspace({ selectedDocId }: Props) {
  const [tab, setTab] = useState<TabId>('chat')

  const subtitle = useMemo(() => {
    if (!selectedDocId) return 'Evidence-grounded research analysis'
    return `Selected doc: ${selectedDocId.slice(0, 8)}…`
  }, [selectedDocId])

  return (
    <div className="workspaceShell">
      <header className="workspaceHeader">
        <div className="workspaceTitleBlock">
          <div className="workspaceKicker">AI</div>
          <div className="workspaceTitle">Research Copilot</div>
          <div className="workspaceSubtitle">{subtitle}</div>
        </div>

        <nav className="tabs">
          <button className={`tab ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>
            Chat
          </button>
          <button className={`tab ${tab === 'claims' ? 'active' : ''}`} onClick={() => setTab('claims')}>
            Claims
          </button>
          <button className={`tab ${tab === 'pdf' ? 'active' : ''}`} onClick={() => setTab('pdf')}>
            PDF Viewer
          </button>
        </nav>
      </header>

      <section className="workspaceBody">
        {tab === 'chat' && (
          <div className="chatShell">
            <div className="chatThread">
              <div className="bubble user">
                What are the main differences between BERT and GPT architectures?
              </div>

              <div className="bubble assistant">
                BERT is trained with masked language modeling to build bidirectional representations, while GPT is
                trained autoregressively to predict the next token left-to-right.
                <div className="citations">
                  <div className="citationHeader">Citations</div>
                  <div className="citationRow">
                    <div className="citationTitle">BERT: Pre-training…</div>
                    <div className="citationMeta">Page 3</div>
                  </div>
                  <div className="citationRow">
                    <div className="citationTitle">GPT-3: Language Models…</div>
                    <div className="citationMeta">Page 5</div>
                  </div>
                </div>
              </div>

              <div className="bubble user">Which approach is better for downstream tasks?</div>
            </div>

            <div className="chatComposer">
              <input className="chatInput" placeholder="Ask a question about your research papers..." />
              <button className="btn btnPrimary">Send</button>
            </div>
          </div>
        )}

        {tab === 'claims' && (
          <div className="emptyState">
            <div className="emptyTitle">Claims</div>
            <div className="muted">We’ll add claim extraction once chat is wired up.</div>
          </div>
        )}

        {tab === 'pdf' && (
          <div className="emptyState">
            <div className="emptyTitle">PDF Viewer</div>
            <div className="muted">
              Select a document in the sidebar, then we can render the PDF here.
              {selectedDocId ? ` (doc_id=${selectedDocId})` : ''}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

