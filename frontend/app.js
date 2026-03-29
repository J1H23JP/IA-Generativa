const API = "";
console.log("app.js cargado (v2)");

// ── Auto-resize textarea ──
const textarea = document.getElementById("question-input");
textarea.addEventListener("input", () => {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
});

textarea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
  }
});

// ── Status y documentos ──
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
      detail.textContent = "Subí un documento para comenzar";
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
    console.log("loadDocuments response", data);
    const list = document.getElementById("doc-list");
    if (!data.documents.length) {
      list.innerHTML = '<li class="doc-item-loading">Sin documentos indexados</li>';
      return;
    }
    list.innerHTML = data.documents
      .map((d) => `<li class="doc-item" data-filename="${encodeURIComponent(d.name)}">
        <span class="doc-name">${d.name}</span>
        <span>${d.chunks} chunks</span>
        <button class="delete-btn" type="button" aria-label="Eliminar documento">✕</button>
      </li>`)
      .join("");

    list.querySelectorAll(".doc-item").forEach((item) => {
      const btn = item.querySelector(".delete-btn");
      const filename = decodeURIComponent(item.getAttribute("data-filename"));
      btn.addEventListener("click", () => deleteDocument(filename));
    });
  } catch {
    document.getElementById("doc-list").innerHTML = '<li class="doc-item-loading">Error al cargar</li>';
  }
}

async function deleteDocument(encodedFilename) {
  const filename = decodeURIComponent(encodedFilename);
  if (!confirm(`¿Estás seguro de que quieres eliminar '${filename}'?`)) return;

  try {
    const res = await fetch(`${API}/api/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
    const data = await res.json();

    if (!res.ok) {
      alert(`Error: ${data.detail}`);
    } else {
      alert(data.message);
      await loadDocuments();
      await loadStatus();
    }
  } catch {
    alert("Error de conexión al eliminar el documento.");
  }
}

function setQuestion(text) {
  textarea.value = text;
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  textarea.focus();
}

// ── Upload de documentos ──
document.getElementById("upload-btn").addEventListener("click", () => {
  document.getElementById("file-input").click();
});

document.getElementById("file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const statusEl = document.getElementById("upload-status");
  const btn = document.getElementById("upload-btn");

  statusEl.textContent = `Subiendo ${file.name}...`;
  statusEl.className = "upload-status uploading";
  btn.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API}/api/upload`, { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      statusEl.textContent = `Error: ${data.detail}`;
      statusEl.className = "upload-status error";
    } else {
      statusEl.textContent = `✓ ${data.message}`;
      statusEl.className = "upload-status success";
      await loadDocuments();
      await loadStatus();
      setTimeout(() => { statusEl.textContent = ""; statusEl.className = "upload-status"; }, 4000);
    }
  } catch {
    statusEl.textContent = "Error de conexión al subir el archivo.";
    statusEl.className = "upload-status error";
  }

  btn.disabled = false;
  e.target.value = "";
});

// ── Chat con streaming ──
document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = textarea.value.trim();
  if (!question) return;

  const messagesEl = document.getElementById("messages");
  const sendBtn = document.getElementById("send-btn");

  const welcome = messagesEl.querySelector(".welcome-msg");
  if (welcome) welcome.remove();

  messagesEl.appendChild(createUserMsg(question));
  textarea.value = "";
  textarea.style.height = "auto";
  sendBtn.disabled = true;

  const thinking = createThinking();
  messagesEl.appendChild(thinking);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const response = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: 4 }),
    });

    if (!response.ok) {
      thinking.remove();
      messagesEl.appendChild(createUserMsg("Error al conectar con el servidor.", true));
      sendBtn.disabled = false;
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let botDiv = null;
    let bubbleEl = null;
    let answer = "";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // Guardar línea incompleta

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") break;

        try {
          const parsed = JSON.parse(raw);

          if (parsed.type === "meta") {
            thinking.remove();
            botDiv = createBotShell(parsed);
            bubbleEl = botDiv.querySelector(".msg-bubble");
            messagesEl.appendChild(botDiv);

          } else if (parsed.type === "token" && bubbleEl) {
            answer += parsed.token;
            bubbleEl.innerHTML = formatAnswer(answer);
            messagesEl.scrollTop = messagesEl.scrollHeight;

          } else if (parsed.type === "error") {
            if (thinking.parentNode) thinking.remove();
            messagesEl.appendChild(createErrorMsg(parsed.message));
          }
        } catch (_) {}
      }
    }
  } catch (err) {
    thinking.remove();
    messagesEl.appendChild(createErrorMsg("Error de conexión. Verificá que el servidor esté corriendo."));
  }

  sendBtn.disabled = false;
  messagesEl.scrollTop = messagesEl.scrollHeight;
});

// ── Helpers de UI ──
function createUserMsg(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `<span class="msg-label">Vos</span><div class="msg-bubble">${escapeHtml(text)}</div>`;
  return div;
}

function createBotShell(meta) {
  const div = document.createElement("div");
  div.className = "msg bot";

  const sourceTags = (meta.sources || [])
    .map((s) => `<span class="source-tag">${s}</span>`)
    .join("");

  const chunkCards = (meta.chunks || [])
    .map((c) => `
      <div class="chunk-card">
        <div class="chunk-meta">
          <span class="chunk-score">Score: ${(c.score * 100).toFixed(1)}%</span>
          <span class="chunk-source">${c.source} — pág. ${c.page}</span>
        </div>
        <div>${escapeHtml(c.text)}${c.text.length >= 200 ? "…" : ""}</div>
      </div>`).join("");

  const chunksId = "chunks-" + Date.now();

  div.innerHTML = `
    <span class="msg-label">Asistente</span>
    <div class="msg-bubble"></div>
    ${sourceTags ? `<div class="msg-sources">${sourceTags}</div>` : ""}
    <button class="chunks-toggle" onclick="toggleChunks('${chunksId}', this)">
      Ver ${meta.chunks_used} fragmentos recuperados ▸
    </button>
    <div id="${chunksId}" class="chunks-detail" style="display:none">${chunkCards}</div>`;
  return div;
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

function createErrorMsg(text) {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = `<span class="msg-label">Asistente</span><div class="msg-bubble" style="color:#ef4444">${escapeHtml(text)}</div>`;
  return div;
}

function toggleChunks(id, btn) {
  const el = document.getElementById(id);
  const visible = el.style.display !== "none";
  el.style.display = visible ? "none" : "flex";
  btn.textContent = visible
    ? `Ver ${el.children.length} fragmentos recuperados ▸`
    : "Ocultar fragmentos ▴";
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function formatAnswer(text) {
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/\n/g, "<br>");
  return text;
}

// Init
loadStatus();
loadDocuments();
