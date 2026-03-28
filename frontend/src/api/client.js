const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    const detail = data.detail || data.response || "Request failed";
    throw new Error(detail);
  }

  return {
    data,
    headers: response.headers,
  };
}

export async function sendChatMessage(payload) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function resetSession(sessionId) {
  return request(`/reset/${encodeURIComponent(sessionId)}`, {
    method: "POST",
  });
}

export async function rebuildRagIndex() {
  return request("/rag/reindex", {
    method: "POST",
  });
}

export async function fetchHealth() {
  return request("/", {
    method: "GET",
  });
}

