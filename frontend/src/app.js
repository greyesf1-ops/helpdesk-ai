const state = {
  conversations: [],
  currentConversationId: null,
  isSending: false,
  searchTerm: "",
};

const elements = {
  conversationList: document.querySelector("#conversationList"),
  newConversation: document.querySelector("#newConversation"),
  conversationTitle: document.querySelector("#conversationTitle"),
  conversationSearch: document.querySelector("#conversationSearch"),
  statusBadge: document.querySelector("#statusBadge"),
  messages: document.querySelector("#messages"),
  messageForm: document.querySelector("#messageForm"),
  messageInput: document.querySelector("#messageInput"),
  attachmentInput: document.querySelector("#attachmentInput"),
  attachmentButton: document.querySelector("#attachmentButton"),
  attachmentPreview: document.querySelector("#attachmentPreview"),
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
    day: "numeric",
    month: "numeric",
    year: "2-digit",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function setStatus(text, ok = true) {
  elements.statusBadge.textContent = ok ? "En linea" : text;
  elements.statusBadge.classList.toggle("offline", !ok);
}

function getConversationTone(title) {
  const normalized = title.toLowerCase();
  if (normalized.includes("correo") || normalized.includes("mail")) return "mail";
  if (normalized.includes("red") || normalized.includes("internet") || normalized.includes("wifi")) return "network";
  if (normalized.includes("acceso") || normalized.includes("password")) return "warning";
  if (normalized.includes("adjunto") || normalized.includes("captura")) return "file";
  return "chat";
}

function getConversationIcon(tone) {
  const icons = {
    mail: "M",
    network: "W",
    warning: "!",
    file: "I",
    chat: "C",
  };
  return icons[tone] || "C";
}

function renderConversations() {
  elements.conversationList.innerHTML = "";
  const filtered = state.conversations.filter((conversation) =>
    conversation.title.toLowerCase().includes(state.searchTerm.toLowerCase()),
  );

  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "conversation-empty";
    empty.textContent = state.searchTerm ? "Sin resultados" : "Crea una consulta";
    elements.conversationList.appendChild(empty);
    return;
  }

  filtered.forEach((conversation) => {
    const tone = getConversationTone(conversation.title);
    const button = document.createElement("button");
    button.className = `conversation-item tone-${tone}`;
    if (conversation.id === state.currentConversationId) {
      button.classList.add("active");
    }
    button.innerHTML = `
      <span class="conversation-icon">${getConversationIcon(tone)}</span>
      <span class="conversation-copy">
        <strong>${escapeHtml(conversation.title)}</strong>
        <span>${formatDate(conversation.updated_at)}</span>
      </span>
    `;
    button.addEventListener("click", () => selectConversation(conversation.id));
    elements.conversationList.appendChild(button);
  });
}

function formatAssistantContent(content) {
  return content
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const match = line.match(/^(\d+)\.\s+(.*)$/);
      if (match) {
        return `<span class="step-line"><span>${match[1]}</span>${escapeHtml(match[2])}</span>`;
      }
      return `<span class="text-line">${escapeHtml(line)}</span>`;
    })
    .join("");
}

function renderMessages(messages) {
  elements.messages.innerHTML = "";

  if (!messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `
      <strong>Listo para atender soporte tecnico</strong>
      <span>Describe un problema o adjunta una captura para iniciar el diagnostico.</span>
    `;
    elements.messages.appendChild(empty);
    return;
  }

  messages.forEach((message) => {
    const row = document.createElement("div");
    row.className = `message-row ${message.role}`;
    const attachment = message.attachment_url
      ? `<a class="message-attachment" href="${message.attachment_url}" target="_blank" rel="noreferrer">
          <img src="${message.attachment_url}" alt="Captura adjunta del caso" />
        </a>`
      : "";
    const content =
      message.role === "assistant"
        ? formatAssistantContent(message.content)
        : `<span class="text-line">${escapeHtml(message.content)}</span>`;

    row.innerHTML = `
      ${message.role === "assistant" ? '<span class="bot-avatar" aria-hidden="true"></span>' : ""}
      <article class="message ${message.role}">
        ${
          message.role === "assistant"
            ? `<div class="message-meta"><strong>HelpDesk AI</strong>${
                message.category ? `<span class="category">${escapeHtml(message.category)}</span>` : ""
              }</div>`
            : ""
        }
        <div class="message-content">${content}</div>
        ${attachment}
        <div class="message-footer">
          <span>${formatDate(message.created_at)}</span>
          ${message.role === "assistant" ? "<span>Me gusta</span><span>Revisar</span>" : "<span>OK</span>"}
        </div>
      </article>
      ${message.role === "user" ? '<span class="user-avatar" aria-hidden="true">U</span>' : ""}
    `;
    elements.messages.appendChild(row);
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

function renderAttachmentPreview() {
  const file = elements.attachmentInput.files?.[0];
  if (!file) {
    elements.attachmentPreview.classList.add("hidden");
    elements.attachmentPreview.innerHTML = "";
    return;
  }

  elements.attachmentPreview.classList.remove("hidden");
  elements.attachmentPreview.innerHTML = `
    <span>${escapeHtml(file.name)}</span>
    <button id="removeAttachment" type="button">Quitar</button>
  `;
  document.querySelector("#removeAttachment").addEventListener("click", () => {
    elements.attachmentInput.value = "";
    renderAttachmentPreview();
  });
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
  const attachment = elements.attachmentInput.files?.[0] || null;
  elements.messageInput.value = "";
  setStatus("Procesando");

  try {
    if (attachment) {
      const formData = new FormData();
      formData.append("content", content);
      formData.append("attachment", attachment);
      const response = await fetch(
        `/api/conversations/${state.currentConversationId}/messages-with-attachment`,
        {
          method: "POST",
          body: formData,
        },
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
    } else {
      await api(`/api/conversations/${state.currentConversationId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
    }
    elements.attachmentInput.value = "";
    renderAttachmentPreview();
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
elements.attachmentButton.addEventListener("click", () => elements.attachmentInput.click());
elements.attachmentInput.addEventListener("change", renderAttachmentPreview);
elements.conversationSearch.addEventListener("input", (event) => {
  state.searchTerm = event.target.value;
  renderConversations();
});
boot();
