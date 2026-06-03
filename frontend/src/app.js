const state = {
  conversations: [],
  currentConversationId: null,
  isSending: false,
};

const elements = {
  conversationList: document.querySelector("#conversationList"),
  newConversation: document.querySelector("#newConversation"),
  conversationTitle: document.querySelector("#conversationTitle"),
  statusBadge: document.querySelector("#statusBadge"),
  messages: document.querySelector("#messages"),
  messageForm: document.querySelector("#messageForm"),
  messageInput: document.querySelector("#messageInput"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Error de API");
  }

  return response.json();
}

function formatDate(value) {
  return new Intl.DateTimeFormat("es-GT", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function setStatus(text, ok = true) {
  elements.statusBadge.textContent = text;
  elements.statusBadge.style.background = ok ? "#dff6f1" : "#ffe8d6";
  elements.statusBadge.style.color = ok ? "#12695e" : "#9b4d12";
}

function renderConversations() {
  elements.conversationList.innerHTML = "";

  if (!state.conversations.length) {
    const empty = document.createElement("div");
    empty.className = "conversation-item";
    empty.innerHTML = "<strong>Sin historial</strong><span>Crea una consulta</span>";
    elements.conversationList.appendChild(empty);
    return;
  }

  state.conversations.forEach((conversation) => {
    const button = document.createElement("button");
    button.className = "conversation-item";
    if (conversation.id === state.currentConversationId) {
      button.classList.add("active");
    }
    button.innerHTML = `
      <strong>${escapeHtml(conversation.title)}</strong>
      <span>${formatDate(conversation.updated_at)}</span>
    `;
    button.addEventListener("click", () => selectConversation(conversation.id));
    elements.conversationList.appendChild(button);
  });
}

function renderMessages(messages) {
  elements.messages.innerHTML = "";

  if (!messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Describe un problema tecnico para iniciar el diagnostico.";
    elements.messages.appendChild(empty);
    return;
  }

  messages.forEach((message) => {
    const article = document.createElement("article");
    article.className = `message ${message.role}`;
    article.innerHTML = `
      <div class="message-meta">
        <span>${message.role === "user" ? "Usuario" : "HelpDesk AI"}</span>
        ${message.category ? `<span class="category">${escapeHtml(message.category)}</span>` : ""}
      </div>
      <p>${escapeHtml(message.content)}</p>
    `;
    elements.messages.appendChild(article);
  });

  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadConversations() {
  state.conversations = await api("/api/conversations");
  if (!state.currentConversationId && state.conversations.length) {
    state.currentConversationId = state.conversations[0].id;
  }
  renderConversations();
}

async function selectConversation(id) {
  state.currentConversationId = id;
  const selected = state.conversations.find((item) => item.id === id);
  elements.conversationTitle.textContent = selected?.title || "Consulta de soporte";
  renderConversations();
  const messages = await api(`/api/conversations/${id}/messages`);
  renderMessages(messages);
}

async function createConversation() {
  const conversation = await api("/api/conversations", {
    method: "POST",
    body: JSON.stringify({ title: "Nueva conversacion" }),
  });
  state.currentConversationId = conversation.id;
  await loadConversations();
  await selectConversation(conversation.id);
  elements.messageInput.focus();
}

async function sendMessage(event) {
  event.preventDefault();
  if (state.isSending) return;

  const content = elements.messageInput.value.trim();
  if (!content) return;

  if (!state.currentConversationId) {
    await createConversation();
  }

  state.isSending = true;
  elements.messageInput.value = "";
  setStatus("Procesando");

  try {
    await api(`/api/conversations/${state.currentConversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    await loadConversations();
    await selectConversation(state.currentConversationId);
    setStatus("Operativo");
  } catch (error) {
    setStatus("Error", false);
    alert("No se pudo enviar el mensaje. Revisa los contenedores del backend.");
  } finally {
    state.isSending = false;
  }
}

async function boot() {
  try {
    await api("/api/health");
    setStatus("Operativo");
    await loadConversations();
    if (state.currentConversationId) {
      await selectConversation(state.currentConversationId);
    } else {
      await createConversation();
    }
  } catch (error) {
    setStatus("Sin conexion", false);
    renderMessages([]);
  }
}

elements.newConversation.addEventListener("click", createConversation);
elements.messageForm.addEventListener("submit", sendMessage);
boot();

