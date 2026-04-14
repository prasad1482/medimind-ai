/**
 * MediMind AI — Frontend Application Logic
 * Professional Medical Dark-Blue Edition
 * Handles: chat UI, API calls, markdown rendering, sidebar topics, particle canvas
 */

const API_BASE = "http://localhost:5000";

// ── DOM References ────────────────────────────────────────
const chatContainer  = document.getElementById("chatContainer");
const messagesList   = document.getElementById("messagesList");
const welcomeScreen  = document.getElementById("welcomeScreen");
const queryInput     = document.getElementById("queryInput");
const sendBtn        = document.getElementById("sendBtn");
const sendIcon       = document.getElementById("sendIcon");
const loadingRing    = document.getElementById("loadingRing");
const charCount      = document.getElementById("charCount");
const statusDot      = document.getElementById("statusDot");
const statusText     = document.getElementById("statusText");
const vectorCount    = document.getElementById("vectorCount");
const newChatBtn     = document.getElementById("newChatBtn");
const sidebarToggle  = document.getElementById("sidebarToggle");
const sidebar        = document.getElementById("sidebar");
const mainContent    = document.getElementById("mainContent");

// ── App State ─────────────────────────────────────────────
let isLoading = false;
let conversationStarted = false;

// ══════════════════════════════════════════════════════════
// PARTICLE CANVAS ANIMATION
// ══════════════════════════════════════════════════════════
(function initParticles() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let particles = [];

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticle() {
    // Medical-themed: navy/teal hues
    const hueOpts = [200, 210, 220, 185, 195]; // deep blues + teal
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.4 + 0.2,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      alpha: Math.random() * 0.45 + 0.08,
      hue: hueOpts[Math.floor(Math.random() * hueOpts.length)],
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: 100 }, createParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue}, 80%, 60%, ${p.alpha})`;
      ctx.fill();
    });

    // Draw connections for nearby particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 75) {
          ctx.beginPath();
          ctx.strokeStyle = `hsla(205, 80%, 55%, ${0.05 * (1 - dist / 75)})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize);
  init();
  draw();
})();

// ══════════════════════════════════════════════════════════
// HEALTH CHECK
// ══════════════════════════════════════════════════════════
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, {
      signal: AbortSignal.timeout(8000)
    });

    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const data = await res.json();

    statusDot.className  = "status-dot online";
    statusText.textContent = "MediMind AI Online";

    if (data.vectors_indexed != null) {
      vectorCount.textContent = Number(data.vectors_indexed).toLocaleString();
    }
  } catch {
    statusDot.className  = "status-dot error";
    statusText.textContent = "Server Offline — Run: python run.py";
    vectorCount.textContent = "—";
  }
}

checkHealth();
setInterval(checkHealth, 30000);

// ══════════════════════════════════════════════════════════
// SIDEBAR TOGGLE
// ══════════════════════════════════════════════════════════
sidebarToggle.addEventListener("click", () => {
  sidebar.classList.toggle("hidden");
  mainContent.classList.toggle("full-width");
});

// ══════════════════════════════════════════════════════════
// SIDEBAR CAPABILITY ITEMS — make them send queries
// ══════════════════════════════════════════════════════════
function attachSidebarItems() {
  // Capability items (li.cap-item)
  document.querySelectorAll(".cap-item[data-query]").forEach(item => {
    const handler = () => {
      const q = item.dataset.query;
      if (!q) return;
      // On mobile: close sidebar first
      if (window.innerWidth <= 768) {
        sidebar.classList.remove("visible");
      }
      setInputQuery(q);
      sendMessage();
    };

    item.addEventListener("click", handler);
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handler();
      }
    });
  });

  // Quick list items (li.quick-item)
  document.querySelectorAll(".quick-item[data-query]").forEach(item => {
    const handler = () => {
      const q = item.dataset.query;
      if (!q) return;
      if (window.innerWidth <= 768) {
        sidebar.classList.remove("visible");
      }
      setInputQuery(q);
      sendMessage();
    };

    item.addEventListener("click", handler);
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handler();
      }
    });
  });
}

function setInputQuery(q) {
  queryInput.value = q;
  autoResize(queryInput);
  updateCharCount();
  updateSendBtn();
}

// ══════════════════════════════════════════════════════════
// SUGGESTION CARDS
// ══════════════════════════════════════════════════════════
function attachSuggestionCards() {
  document.querySelectorAll(".suggestion-card").forEach(card => {
    card.addEventListener("click", () => {
      const q = card.dataset.query;
      if (!q) return;
      setInputQuery(q);
      sendMessage();
    });
  });
}

// ══════════════════════════════════════════════════════════
// NEW CHAT
// ══════════════════════════════════════════════════════════
newChatBtn.addEventListener("click", () => {
  messagesList.innerHTML = "";
  welcomeScreen.style.display = "flex";
  conversationStarted = false;
  queryInput.value = "";
  updateCharCount();
  updateSendBtn();
  queryInput.focus();
});

// ══════════════════════════════════════════════════════════
// INPUT HANDLING
// ══════════════════════════════════════════════════════════
queryInput.addEventListener("input", () => {
  autoResize(queryInput);
  updateCharCount();
  updateSendBtn();
});

queryInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!isLoading && queryInput.value.trim()) {
      sendMessage();
    }
  }
});

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

function updateCharCount() {
  const len = queryInput.value.length;
  charCount.textContent = `${len} / 1000`;
  charCount.className =
    len > 900 ? "char-count limit" :
    len > 700 ? "char-count warn" :
    "char-count";
}

function updateSendBtn() {
  sendBtn.disabled = !queryInput.value.trim() || isLoading;
}

sendBtn.addEventListener("click", () => {
  if (!isLoading && queryInput.value.trim()) sendMessage();
});

// ══════════════════════════════════════════════════════════
// SEND MESSAGE — Core Chat Logic
// ══════════════════════════════════════════════════════════
async function sendMessage() {
  const query = queryInput.value.trim();
  if (!query || isLoading) return;

  // Hide welcome screen on first message
  if (!conversationStarted) {
    welcomeScreen.style.display = "none";
    conversationStarted = true;
  }

  // Clear input + set loading
  queryInput.value = "";
  queryInput.style.height = "auto";
  updateCharCount();
  setLoading(true);

  // Render user message immediately
  appendUserMessage(query);

  // Show AI typing indicator
  const typingEl = appendTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ query, stream: false }),
    });

    const data = await res.json();
    typingEl.remove();

    if (res.ok) {
      appendAIMessage(data.answer, data.sources || [], data.time_taken);
    } else {
      appendErrorMessage(data.error || "An error occurred. Please try again.");
    }
  } catch (err) {
    typingEl.remove();
    if (err.name === "AbortError" || err.name === "TimeoutError") {
      appendErrorMessage("Request timed out. Please check if the server is running.");
    } else {
      appendErrorMessage(
        "Cannot connect to MediMind AI server. Please start the backend:\n\npython run.py"
      );
    }
  } finally {
    setLoading(false);
    scrollToBottom();
    queryInput.focus();
  }
}

// ══════════════════════════════════════════════════════════
// MESSAGE RENDERING
// ══════════════════════════════════════════════════════════
function appendUserMessage(text) {
  const el = document.createElement("div");
  el.className = "message user-message";
  el.setAttribute("role", "listitem");
  el.innerHTML = `
    <div class="avatar user-avatar" aria-hidden="true">You</div>
    <div class="bubble">
      <p class="bubble-text">${escapeHTML(text)}</p>
      <div class="bubble-meta">
        <span class="time-stamp">${getTimeStr()}</span>
      </div>
    </div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
}

function appendTypingIndicator() {
  const el = document.createElement("div");
  el.className = "message ai-message";
  el.id = "typing-msg";
  el.setAttribute("role", "listitem");
  el.innerHTML = `
    <div class="avatar ai-avatar" aria-hidden="true">
      ${aiAvatarSVG()}
    </div>
    <div class="bubble" aria-label="MediMind is thinking">
      <div class="typing-indicator" aria-label="Loading response">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
  return el;
}

function appendAIMessage(text, sources, timeTaken) {
  const el = document.createElement("div");
  el.className = "message ai-message";
  el.setAttribute("role", "listitem");

  const sourcesHTML     = buildSourcesHTML(sources);
  const formattedText   = formatMedicalText(text);
  const uid             = Date.now();

  el.innerHTML = `
    <div class="avatar ai-avatar" aria-hidden="true">
      ${aiAvatarSVG(uid)}
    </div>
    <div class="bubble">
      <div class="bubble-text">${formattedText}</div>
      ${sourcesHTML}
      <div class="bubble-meta">
        <span class="time-stamp">${getTimeStr()}</span>
        ${timeTaken ? `<span class="response-time">${timeTaken}s</span>` : ""}
      </div>
    </div>
  `;

  messagesList.appendChild(el);

  // Wire sources toggle
  const toggle = el.querySelector(".sources-toggle");
  const list   = el.querySelector(".sources-list");
  if (toggle && list) {
    toggle.addEventListener("click", () => {
      const isOpen = toggle.classList.toggle("open");
      list.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });
  }

  scrollToBottom();
}

function appendErrorMessage(text) {
  const el = document.createElement("div");
  el.className = "message ai-message";
  el.setAttribute("role", "listitem");
  el.innerHTML = `
    <div class="avatar ai-avatar" aria-hidden="true">⚠️</div>
    <div class="bubble error-bubble">
      <p class="bubble-text">${escapeHTML(text)}</p>
      <div class="bubble-meta">
        <span class="time-stamp">${getTimeStr()}</span>
      </div>
    </div>
  `;
  messagesList.appendChild(el);
  scrollToBottom();
}

// ── Reusable AI avatar SVG ────────────────────────────────
function aiAvatarSVG(uid = 0) {
  return `
    <svg viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg" width="22" height="22">
      <path d="M22 8v28M8 22h28" stroke="url(#ag${uid})" stroke-width="4" stroke-linecap="round"/>
      <defs>
        <linearGradient id="ag${uid}" x1="8" y1="8" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop stop-color="#00b4cc"/>
          <stop offset="1" stop-color="#1d4ed8"/>
        </linearGradient>
      </defs>
    </svg>
  `;
}

// ══════════════════════════════════════════════════════════
// SOURCES ACCORDION HTML
// ══════════════════════════════════════════════════════════
function buildSourcesHTML(sources) {
  if (!sources || sources.length === 0) return "";

  const chips = sources.map((s) => `
    <div class="source-chip">
      <div class="source-chip-header">
        <span class="page-badge">📄 Page ${s.page}</span>
        <span class="rel-score">Relevance: ${(s.score * 100).toFixed(0)}%</span>
      </div>
      <p class="source-excerpt">"${escapeHTML(s.excerpt)}"</p>
    </div>
  `).join("");

  return `
    <div class="sources-accordion">
      <button class="sources-toggle" aria-expanded="false">
        📚 ${sources.length} Source${sources.length > 1 ? "s" : ""} from Medical Book
        <span class="chevron">▼</span>
      </button>
      <div class="sources-list">
        ${chips}
      </div>
    </div>
  `;
}

// ══════════════════════════════════════════════════════════
// TEXT FORMATTING — medical markdown
// ══════════════════════════════════════════════════════════
function formatMedicalText(text) {
  if (!text) return "";

  return escapeHTML(text)
    // Bold: **text**
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    // Italic: *text*
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>")
    // H2 headers: ## text
    .replace(/^## (.+)$/gm,
      '<span style="display:block;font-size:1.02rem;font-weight:700;color:var(--teal-light);margin:14px 0 5px;letter-spacing:-0.01em;">$1</span>')
    // H3 headers: ### text
    .replace(/^### (.+)$/gm,
      '<span style="display:block;font-size:0.92rem;font-weight:600;color:var(--text-primary);margin:10px 0 3px;">$1</span>')
    // Bullet points: - text
    .replace(/^[\-•] (.+)$/gm,
      '<span style="display:block;padding-left:18px;position:relative;margin:3px 0;">' +
      '<span style="position:absolute;left:0;color:var(--teal);font-weight:600;">›</span>$1</span>')
    // Numbered lists: 1. text
    .replace(/^(\d+)\. (.+)$/gm,
      '<span style="display:block;padding-left:22px;position:relative;margin:3px 0;">' +
      '<span style="position:absolute;left:0;color:var(--teal);font-size:0.82em;font-weight:700;">$1.</span>$2</span>')
    // Inline code: `code`
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Page citations: (Medical Book, p. X) or (p. X)
    .replace(/\(Medical Book, p\. (\d+)\)/g,
      '<span style="background:rgba(0,100,200,0.14);border:1px solid rgba(0,180,204,0.22);border-radius:4px;padding:1px 6px;font-size:0.78em;color:var(--teal);font-weight:600;">📄 p.$1</span>')
    .replace(/\(p\. (\d+)\)/g,
      '<span style="background:rgba(0,100,200,0.14);border:1px solid rgba(0,180,204,0.22);border-radius:4px;padding:1px 6px;font-size:0.78em;color:var(--teal);font-weight:600;">📄 p.$1</span>')
    // Newlines → <br>
    .replace(/\n/g, "<br>");
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g,  "&amp;")
    .replace(/</g,  "&lt;")
    .replace(/>/g,  "&gt;")
    .replace(/"/g,  "&quot;")
    .replace(/'/g,  "&#039;");
}

// ══════════════════════════════════════════════════════════
// UTILITY
// ══════════════════════════════════════════════════════════
function setLoading(val) {
  isLoading          = val;
  sendBtn.disabled   = val;
  sendIcon.hidden    = val;
  loadingRing.hidden = !val;
  queryInput.disabled = val;
  updateSendBtn();
}

function scrollToBottom() {
  chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: "smooth" });
}

function getTimeStr() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// ══════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════
attachSidebarItems();
attachSuggestionCards();
queryInput.focus();
