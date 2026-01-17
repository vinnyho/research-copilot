import { useMemo, useState, useRef, useEffect } from 'react'
import type { DocumentRow } from '../app/App'

type TabId = 'chat' | 'claims' | 'pdf'

type Citation = {
  doc_id: string
  filename: string
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
  documents: DocumentRow[]
}

export default function Workspace({ documents }: Props) {
  const [tab, setTab] = useState<TabId>('chat')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set())
  const [expandedCitations, setExpandedCitations] = useState<Set<number>>(new Set())
  const threadRef = useRef<HTMLDivElement>(null)

  const readyDocs = useMemo(
    () => documents.filter((d) => d.status === 'ready'),
    [documents]
  )

  const subtitle = useMemo(() => {
    if (selectedDocIds.size === 0) return 'Searching all documents'
    if (selectedDocIds.size === 1) return '1 document selected'
    return `${selectedDocIds.size} documents selected`
  }, [selectedDocIds])

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const toggleDoc = (docId: string) => {
    setSelectedDocIds((prev) => {
      const next = new Set(prev)
      if (next.has(docId)) {
        next.delete(docId)
      } else {
        next.add(docId)
      }
      return next
    })
  }

  const toggleCitation = (idx: number) => {
    setExpandedCitations((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) {
        next.delete(idx)
      } else {
        next.add(idx)
      }
      return next
    })
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    const userMessage: Message = { role: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setExpandedCitations(new Set())

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          history,
          doc_ids: selectedDocIds.size > 0 ? Array.from(selectedDocIds) : null,
          limit: 8,
        }),
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

  const clearChat = () => {
    setMessages([])
    setExpandedCitations(new Set())
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
            {readyDocs.length > 0 && (
              <div className="docFilter">
                <div className="docFilterHeader">
                  <span className="docFilterLabel">Search in:</span>
                  {selectedDocIds.size > 0 && (
                    <button
                      className="docFilterClear"
                      onClick={() => setSelectedDocIds(new Set())}
                    >
                      Clear
                    </button>
                  )}
                </div>
                <div className="docFilterList">
                  {readyDocs.map((d) => (
                    <label key={d.doc_id} className="docFilterItem">
                      <input
                        type="checkbox"
                        checked={selectedDocIds.has(d.doc_id)}
                        onChange={() => toggleDoc(d.doc_id)}
                      />
                      <span className="docFilterName">
                        {d.filename ?? 'Untitled'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="chatThread" ref={threadRef}>
              {messages.length === 0 && (
                <div className="emptyState">
                  <div className="emptyTitle">Start a conversation</div>
                  <div className="muted">
                    Ask questions about your uploaded research papers.
                    {readyDocs.length === 0 && ' Upload a PDF to get started.'}
                  </div>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div key={idx} className={`bubble ${msg.role}`}>
                  <div className="bubbleContent">{msg.content}</div>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations">
                      <div className="citationHeader">
                        Sources ({msg.citations.length})
                      </div>
                      {msg.citations.map((cite, cIdx) => {
                        const globalIdx = idx * 100 + cIdx
                        const isExpanded = expandedCitations.has(globalIdx)
                        return (
                          <div
                            key={cIdx}
                            className={`citationRow ${isExpanded ? 'expanded' : ''}`}
                            onClick={() => toggleCitation(globalIdx)}
                          >
                            <div className="citationMain">
                              <div className="citationTitle">{cite.filename}</div>
                              <div className="citationMeta">Page {cite.page}</div>
                            </div>
                            {isExpanded && (
                              <div className="citationPreview">{cite.content}</div>
                            )}
                          </div>
                        )
                      })}
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
              {messages.length > 0 && (
                <button className="btn btnSmall clearBtn" onClick={clearChat} title="Clear chat">
                  Clear
                </button>
              )}
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
            <div className="muted">Claim extraction coming soon.</div>
          </div>
        )}

        {tab === 'pdf' && (
          <div className="emptyState">
            <div className="emptyTitle">PDF Viewer</div>
            <div className="muted">PDF viewing coming soon.</div>
          </div>
        )}
      </section>
    </div>
  )
}
