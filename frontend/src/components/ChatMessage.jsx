function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <article className={`message-card ${isUser ? "user" : "assistant"}`}>
      <p className="message-role">{isUser ? "You" : "Assistant"}</p>
      <p className="message-text">{message.content}</p>
    </article>
  );
}

export default ChatMessage;

