import { useMemo, useState, useRef, useEffect } from 'react'

type TabId = 'chat' | 'claims' | 'pdf'

type Citation = {
  doc_id: string
  page: number
  chunk_index: number
  content: string
}

type Message = {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

type Props = {
  selectedDocId: string | null
}

export default function Workspace({ selectedDocId }: Props) {
  const [tab, setTab] = useState<TabId>('chat')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const threadRef = useRef<HTMLDivElement>(null)

  const subtitle = useMemo(() => {
    if (!selectedDocId) return 'Evidence-grounded research analysis'
    return `Selected doc: ${selectedDocId.slice(0, 8)}…`
  }, [selectedDocId])


  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

 
    const userMessage: Message = { role: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, limit: 8 }),
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

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
            <div className="chatThread" ref={threadRef}>
              {messages.length === 0 && (
                <div className="emptyState">
                  <div className="emptyTitle">Start a conversation</div>
                  <div className="muted">Ask questions about your uploaded research papers.</div>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div key={idx} className={`bubble ${msg.role}`}>
                  {msg.content}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations">
                      <div className="citationHeader">Sources ({msg.citations.length})</div>
                      {msg.citations.map((cite, cIdx) => (
                        <div key={cIdx} className="citationRow">
                          <div className="citationTitle">
                            Doc {cite.doc_id.slice(0, 8)}…
                          </div>
                          <div className="citationMeta">Page {cite.page}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="bubble assistant loading">
                  <span className="loadingDots">Thinking</span>
                </div>
              )}
            </div>

            <div className="chatComposer">
              <input
                className="chatInput"
                placeholder="Ask a question about your research papers..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
              />
              <button
                className="btn btnPrimary"
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
              >
                {isLoading ? '...' : 'Send'}
              </button>
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

