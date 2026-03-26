const API = "";

// ── Auto-resize textarea ──
const textarea = document.getElementById("question-input");
textarea.addEventListener("input", () => {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
});

// ── Send on Enter (Shift+Enter = newline) ──
textarea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
  }
});

// ── Load status & documents on startup ──
async function loadStatus() {
  try {
    const res = await fetch(`${API}/api/status`);
    const data = await res.json();
    const badge = document.getElementById("status-badge");
    const detail = document.getElementById("status-detail");

    if (data.status === "ok") {
      badge.textContent = "Listo";
      badge.className = "badge badge-ok";
      detail.textContent = `${data.total_chunks} fragmentos indexados`;
    } else {
      badge.textContent = "Sin documentos";
      badge.className = "badge badge-warn";
      detail.textContent = "Ejecutá el ETL primero";
    }
  } catch {
    document.getElementById("status-badge").textContent = "Error";
    document.getElementById("status-badge").className = "badge badge-warn";
  }
}

async function loadDocuments() {
  try {
    const res = await fetch(`${API}/api/documents`);
    const data = await res.json();
    const list = document.getElementById("doc-list");

    if (!data.documents.length) {
      list.innerHTML = '<li class="doc-item-loading">Sin documentos indexados</li>';
      return;
    }

    list.innerHTML = data.documents
      .map(
        (d) => `<li class="doc-item">
          <span class="doc-name">${d.name}</span>
          <span>${d.chunks} chunks</span>
        </li>`
      )
      .join("");
  } catch {
    document.getElementById("doc-list").innerHTML =
      '<li class="doc-item-loading">Error al cargar</li>';
  }
}

// ── Set question from example ──
function setQuestion(text) {
  textarea.value = text;
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  textarea.focus();
}

// ── Chat submit ──
document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = textarea.value.trim();
  if (!question) return;

  const messagesEl = document.getElementById("messages");
  const sendBtn = document.getElementById("send-btn");

  // Clear welcome message
  const welcome = messagesEl.querySelector(".welcome-msg");
  if (welcome) welcome.remove();

  // User bubble
  messagesEl.appendChild(createMsg("user", question));

  // Reset input
  textarea.value = "";
  textarea.style.height = "auto";
  sendBtn.disabled = true;

  // Thinking indicator
  const thinking = createThinking();
  messagesEl.appendChild(thinking);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: 5 }),
    });

    thinking.remove();

    if (!res.ok) {
      const err = await res.json();
      messagesEl.appendChild(createMsg("bot", `Error: ${err.detail}`, null));
    } else {
      const data = await res.json();
      messagesEl.appendChild(createBotMsg(data));
    }
  } catch (err) {
    thinking.remove();
    messagesEl.appendChild(
      createMsg("bot", "Error de conexión. Verificá que el servidor esté corriendo.", null)
    );
  }

  sendBtn.disabled = false;
  messagesEl.scrollTop = messagesEl.scrollHeight;
});

function createMsg(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `
    <span class="msg-label">${role === "user" ? "Vos" : "Asistente"}</span>
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  return div;
}

function createBotMsg(data) {
  const div = document.createElement("div");
  div.className = "msg bot";

  const sourceTags = data.sources
    .map((s) => `<span class="source-tag">${s}</span>`)
    .join("");

  const chunkCards = data.chunks
    .map(
      (c) => `
      <div class="chunk-card">
        <div class="chunk-meta">
          <span class="chunk-score">Score: ${(c.score * 100).toFixed(1)}%</span>
          <span class="chunk-source">${c.source} — pág. ${c.page}</span>
        </div>
        <div>${escapeHtml(c.text)}${c.text.length >= 200 ? "…" : ""}</div>
      </div>`
    )
    .join("");

  const chunksId = "chunks-" + Date.now();

  div.innerHTML = `
    <span class="msg-label">Asistente</span>
    <div class="msg-bubble">${formatAnswer(data.answer)}</div>
    ${sourceTags ? `<div class="msg-sources">${sourceTags}</div>` : ""}
    <button class="chunks-toggle" onclick="toggleChunks('${chunksId}', this)">
      Ver ${data.chunks_used} fragmentos recuperados ▸
    </button>
    <div id="${chunksId}" class="chunks-detail" style="display:none">
      ${chunkCards}
    </div>
  `;
  return div;
}

function toggleChunks(id, btn) {
  const el = document.getElementById(id);
  const visible = el.style.display !== "none";
  el.style.display = visible ? "none" : "flex";
  btn.textContent = visible
    ? `Ver ${el.children.length} fragmentos recuperados ▸`
    : `Ocultar fragmentos ▴`;
}

function createThinking() {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = `
    <span class="msg-label">Asistente</span>
    <div class="thinking">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      Buscando en políticas...
    </div>`;
  return div;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function formatAnswer(text) {
  // Bold **text**
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  // Newlines
  text = text.replace(/\n/g, "<br>");
  return text;
}

// Init
loadStatus();
loadDocuments();
