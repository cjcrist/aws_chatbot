"use client";

import {
  ChangeEvent,
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import { ChatMessage, sendChatMessage } from "../lib/chat";

const USER_ID_STORAGE_KEY = "aws-chatbot-user-id";
const CHAT_HISTORY_STORAGE_KEY = "aws-chatbot-history-v2";

type Msg = ChatMessage & {
  ts: string;
  responseMs?: number;
};

type StoredHistory = Record<string, Msg[]>;

function genUserId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `user-${Date.now().toString(36)}`;
}

function readHistory(): StoredHistory {
  try {
    const raw = sessionStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredHistory) : {};
  } catch {
    return {};
  }
}

function writeHistory(h: StoredHistory) {
  sessionStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(h));
}

function formatDuration(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}:${pad(m)}:${pad(sec)}`;
  return `${pad(m)}:${pad(sec)}`;
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function formatTs(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Page() {
  const [userId, setUserId]         = useState("");
  const [userIdInput, setUserIdInput] = useState("");
  const [messages, setMessages]     = useState<Msg[]>([]);
  const [input, setInput]           = useState("");
  const [isLoading, setIsLoading]   = useState(false);
  const [error, setError]           = useState("");
  const [sessionSecs, setSessionSecs] = useState(0);

  const chatWindowRef = useRef<HTMLDivElement>(null);
  const textareaRef   = useRef<HTMLTextAreaElement>(null);
  const sessionStart  = useRef(Date.now());
  const prevLoading   = useRef<boolean | null>(null);

  // Derived metrics
  const questionCount = messages.filter((m) => m.role === "user").length;
  const responseMessages = messages.filter((m) => m.role === "assistant" && m.responseMs != null);
  const rTimes = responseMessages.map((m) => m.responseMs as number);
  const avgMs  = rTimes.length ? Math.round(rTimes.reduce((a, b) => a + b, 0) / rTimes.length) : null;
  const fastMs = rTimes.length ? Math.min(...rTimes) : null;
  const slowMs = rTimes.length ? Math.max(...rTimes) : null;
  const lastMs = rTimes.length ? rTimes[rTimes.length - 1] : null;

  function focusComposer() {
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      const len = el.value.length;
      el.setSelectionRange(len, len);
    });
  }

  // Session timer
  useEffect(() => {
    const id = setInterval(
      () => setSessionSecs(Math.floor((Date.now() - sessionStart.current) / 1000)),
      1000,
    );
    return () => clearInterval(id);
  }, []);

  // Initialise from sessionStorage
  useEffect(() => {
    const existing = sessionStorage.getItem(USER_ID_STORAGE_KEY);
    const uid = existing || genUserId();
    sessionStorage.setItem(USER_ID_STORAGE_KEY, uid);
    setUserId(uid);
    setUserIdInput(uid);
    const history = readHistory();
    const msgs = history[uid] ?? [];
    setMessages(msgs);
    setTimeout(() => focusComposer(), 50);
  }, []);

  // Persist messages under current userId
  useEffect(() => {
    if (!userId) return;
    const h = readHistory();
    h[userId] = messages;
    writeHistory(h);
  }, [messages, userId]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Refocus textarea after send completes (runs after render so focus sticks)
  useEffect(() => {
    if (prevLoading.current === true && !isLoading) {
      focusComposer();
    }
    prevLoading.current = isLoading;
  }, [isLoading]);

  async function handleSubmit() {
    const query = input.trim();
    if (!query || !userId || isLoading) return;

    setError("");
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    focusComposer();

    const userMsg: Msg = { role: "user", content: query, ts: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    const t0 = Date.now();
    try {
      const res = await sendChatMessage({ query, user_id: userId });
      const responseMs = Date.now() - t0;
      const assistantMsg: Msg = {
        role: "assistant",
        content: res.answer,
        ts: new Date().toISOString(),
        responseMs,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error — please try again.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Something went wrong. Please try again.",
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function onFormSubmit(e: FormEvent) {
    e.preventDefault();
    handleSubmit();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function onInputChange(e: ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }

  function switchUser() {
    const next = userIdInput.trim();
    if (!next || next === userId) return;
    setUserId(next);
    setError("");
    setInput("");
    sessionStorage.setItem(USER_ID_STORAGE_KEY, next);
    const h = readHistory();
    const msgs = h[next] ?? [];
    setMessages(msgs);
    focusComposer();
  }

  function clearSession() {
    const fresh = genUserId();
    setMessages([]);
    setError("");
    setInput("");
    setUserId(fresh);
    setUserIdInput(fresh);
    sessionStart.current = Date.now();
    setSessionSecs(0);
    sessionStorage.removeItem(CHAT_HISTORY_STORAGE_KEY);
    sessionStorage.setItem(USER_ID_STORAGE_KEY, fresh);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    focusComposer();
  }

  const canSend = input.trim().length > 0 && !!userId && !isLoading;

  return (
    <div className="app-shell">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-icon">⚡</span>
          <span className="brand-name">AWS AI Webchat</span>
        </div>

        <div className="header-controls">
          <div className="user-switcher">
            <span className="field-label">Thread</span>
            <input
              className="user-input"
              value={userIdInput}
              onChange={(e) => setUserIdInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && switchUser()}
              placeholder="user_id"
              spellCheck={false}
            />
            <button
              className="btn btn-outline"
              onClick={switchUser}
              disabled={!userIdInput.trim() || userIdInput.trim() === userId}
            >
              Switch
            </button>
          </div>
          <button className="btn btn-danger" onClick={clearSession}>
            Clear session
          </button>
        </div>
      </header>

      <div className="content-shell">
        {/* ── Main row ── */}
        <div className="main-row">
          {/* ── Chat column ── */}
          <section className="chat-col">
          <div className="chat-window" ref={chatWindowRef}>
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-glyph">🤖</div>
                <p className="empty-title">AWS AI Assistant</p>
                <p className="empty-sub">
                  Ask about S3 buckets, IAM users, EC2 instances, and more.
                </p>
              </div>
            ) : (
              messages.map((msg, i) => (
                <article key={i} className={`message ${msg.role}`}>
                  <div className="msg-avatar">
                    {msg.role === "user" ? "👤" : "🤖"}
                  </div>
                  <div className="msg-body">
                    <div className="msg-meta">
                      <span className="msg-author">
                        {msg.role === "user"
                          ? userId.length > 16 ? userId.slice(0, 8) + "…" + userId.slice(-4) : userId
                          : "AWS Assistant"}
                      </span>
                      <span className="msg-ts">{formatTs(msg.ts)}</span>
                      {msg.role === "assistant" && msg.responseMs != null && (
                        <span className="msg-speed">
                          {(msg.responseMs / 1000).toFixed(1)}s
                        </span>
                      )}
                    </div>
                    <div className="msg-content">{msg.content}</div>
                  </div>
                </article>
              ))
            )}

            {isLoading && (
              <article className="message assistant">
                <div className="msg-avatar">🤖</div>
                <div className="msg-body">
                  <div className="msg-meta">
                    <span className="msg-author">AWS Assistant</span>
                    <span className="msg-ts thinking-label">thinking…</span>
                  </div>
                  <div className="thinking-dots">
                    <span /><span /><span />
                  </div>
                </div>
              </article>
            )}
          </div>

          {/* ── Composer ── */}
          <div className="composer">
            {error && (
              <div className="error-banner">
                <span>⚠</span>
                <span>{error}</span>
              </div>
            )}
            <form className="composer-form" onSubmit={onFormSubmit}>
              <textarea
                ref={textareaRef}
                className="composer-input"
                value={input}
                onChange={onInputChange}
                onKeyDown={onKeyDown}
                placeholder="Message AWS Assistant…"
                rows={1}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={!canSend}
                aria-label="Send"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="19" x2="12" y2="5" />
                  <polyline points="5 12 12 5 19 12" />
                </svg>
              </button>
            </form>
            <p className="composer-hint">
              ↵ Enter to send &nbsp;·&nbsp; ⇧ Shift+Enter for new line
            </p>
          </div>
          </section>

        {/* ── Stats sidebar ── */}
        <aside className="stats-sidebar">
          <div className="panel-heading">Session Metrics</div>

          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-value">{questionCount}</div>
              <div className="stat-label">Questions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{formatDuration(sessionSecs)}</div>
              <div className="stat-label">Duration</div>
            </div>
            <div className="stat-card">
              <div className={`stat-value ${avgMs != null ? "c-accent" : ""}`}>
                {avgMs != null ? `${(avgMs / 1000).toFixed(1)}s` : "—"}
              </div>
              <div className="stat-label">Avg Resp.</div>
            </div>
            <div className="stat-card">
              <div className={`stat-value ${fastMs != null ? "c-green" : ""}`}>
                {fastMs != null ? `${(fastMs / 1000).toFixed(1)}s` : "—"}
              </div>
              <div className="stat-label">Fastest</div>
            </div>
            <div className="stat-card">
              <div className={`stat-value ${slowMs != null ? "c-yellow" : ""}`}>
                {slowMs != null ? `${(slowMs / 1000).toFixed(1)}s` : "—"}
              </div>
              <div className="stat-label">Slowest</div>
            </div>
            <div className="stat-card">
              <div className={`stat-value ${lastMs != null ? "c-accent" : ""}`}>
                {lastMs != null ? `${(lastMs / 1000).toFixed(1)}s` : "—"}
              </div>
              <div className="stat-label">Last Resp.</div>
            </div>
          </div>

          <div className="thread-card">
            <div className="thread-card-label">
              <span className="status-dot" />
              Active thread
            </div>
            <div className="thread-card-id">{userId || "—"}</div>
          </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
