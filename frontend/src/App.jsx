import { useEffect, useState } from "react";
import ChatMessage from "./components/ChatMessage";
import MetricCard from "./components/MetricCard";
import {
  fetchHealth,
  rebuildRagIndex,
  resetSession,
  sendChatMessage,
} from "./api/client";

const initialTokenUsage = {
  estimated_input_tokens: 0,
  estimated_output_tokens: 0,
  estimated_total_tokens: 0,
  estimation_method: "approx_chars_div_4",
};

function App() {
  const [sessionId, setSessionId] = useState("default");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Ask about any student record. I can use SQL tools and RAG context from the indexed student database.",
    },
  ]);
  const [tokenUsage, setTokenUsage] = useState(initialTokenUsage);
  const [serverStatus, setServerStatus] = useState("Checking backend...");
  const [actionStatus, setActionStatus] = useState("Ready");
  const [isSending, setIsSending] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadHealth() {
      try {
        const { data } = await fetchHealth();
        if (!ignore) {
          setServerStatus(data.status || "Backend reachable");
        }
      } catch (error) {
        if (!ignore) {
          setServerStatus(`Backend unavailable: ${error.message}`);
        }
      }
    }

    loadHealth();
    return () => {
      ignore = true;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();

    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) {
      return;
    }

    setIsSending(true);
    setActionStatus("Sending message...");
    setMessages((current) => [
      ...current,
      { role: "user", content: trimmedMessage },
    ]);
    setMessage("");

    try {
      const { data } = await sendChatMessage({
        message: trimmedMessage,
        session_id: sessionId,
      });

      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.response },
      ]);
      setTokenUsage(data.token_usage || initialTokenUsage);
      setActionStatus("Last response received successfully.");
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: `Request failed: ${error.message}`,
        },
      ]);
      setActionStatus("Message failed.");
    } finally {
      setIsSending(false);
    }
  }

  async function handleReset() {
    setActionStatus("Clearing conversation memory...");
    try {
      await resetSession(sessionId);
      setMessages([
        {
          role: "assistant",
          content: "Session memory cleared. Start a fresh conversation whenever you are ready.",
        },
      ]);
      setTokenUsage(initialTokenUsage);
      setActionStatus(`Memory reset for session "${sessionId}".`);
    } catch (error) {
      setActionStatus(`Reset failed: ${error.message}`);
    }
  }

  async function handleReindex() {
    if (isReindexing) {
      return;
    }

    setIsReindexing(true);
    setActionStatus("Rebuilding the RAG index...");

    try {
      const { data } = await rebuildRagIndex();
      setActionStatus(
        `${data.status}. Indexed ${data.documents_indexed} student documents.`
      );
    } catch (error) {
      setActionStatus(`Reindex failed: ${error.message}`);
    } finally {
      setIsReindexing(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Students AI Bot</p>
          <h1>Chat with a student database agent backed by RAG and live token estimates.</h1>
          <p className="hero-text">
            This frontend talks to the FastAPI backend, shows per-request token estimates,
            lets you rebuild the vector index, and keeps session-based conversations easy to test.
          </p>
        </div>

        <div className="hero-status">
          <MetricCard label="Backend" value={serverStatus} helper="Live health check from the API." />
          <MetricCard label="Session" value={sessionId} helper="Used for backend memory tracking." />
          <MetricCard
            label="RAG"
            value="SQLite vector store"
            helper="Student rows are embedded and retrieved before model calls."
          />
        </div>
      </section>

      <section className="workspace-grid">
        <div className="panel controls-panel">
          <div className="panel-heading">
            <h2>Controls</h2>
            <p>Update the active session, manage memory, and refresh the retrieval index.</p>
          </div>

          <label className="field">
            <span>Session ID</span>
            <input
              value={sessionId}
              onChange={(event) => setSessionId(event.target.value)}
              placeholder="default"
            />
          </label>

          <div className="button-row">
            <button type="button" className="secondary-button" onClick={handleReset}>
              Reset Memory
            </button>
            <button type="button" className="secondary-button" onClick={handleReindex}>
              {isReindexing ? "Reindexing..." : "Rebuild RAG Index"}
            </button>
          </div>

          <div className="panel-heading metrics-heading">
            <h2>Token Usage</h2>
            <p>Approximate values returned by backend middleware for the latest request.</p>
          </div>

          <div className="metrics-grid">
            <MetricCard
              label="Input"
              value={tokenUsage.estimated_input_tokens}
              helper="Estimated prompt/request tokens."
            />
            <MetricCard
              label="Output"
              value={tokenUsage.estimated_output_tokens}
              helper="Estimated response tokens."
            />
            <MetricCard
              label="Total"
              value={tokenUsage.estimated_total_tokens}
              helper={tokenUsage.estimation_method}
            />
          </div>

          <div className="status-strip">{actionStatus}</div>
        </div>

        <div className="panel chat-panel">
          <div className="panel-heading">
            <h2>Chat</h2>
            <p>Ask for student details, marks, courses, or broader questions that benefit from retrieval.</p>
          </div>

          <div className="message-list">
            {messages.map((entry, index) => (
              <ChatMessage key={`${entry.role}-${index}`} message={entry} />
            ))}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <label className="field">
              <span>Message</span>
              <textarea
                rows="5"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Example: Get me details of Student 42"
              />
            </label>
            <button type="submit" className="primary-button" disabled={isSending}>
              {isSending ? "Sending..." : "Send Message"}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}

export default App;

