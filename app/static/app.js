/* SBI Smart Agent - logic giao diện chat */
(() => {
  "use strict";

  const chatEl = document.getElementById("chat");
  const welcomeEl = document.getElementById("welcome");
  const suggestionsEl = document.getElementById("suggestions");
  const formEl = document.getElementById("chatForm");
  const inputEl = document.getElementById("input");
  const sendBtn = document.getElementById("sendBtn");
  const resetBtn = document.getElementById("resetBtn");

  /** Lịch sử hội thoại gửi lên server: [{role, content}, ...] */
  let history = [];
  let busy = false;

  // ----------------------- Tiện ích render an toàn -----------------------

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  /** Chuyển văn bản thô của bot thành HTML an toàn (đậm, gạch đầu dòng, đoạn). */
  function formatMessage(text) {
    const esc = escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    const lines = esc.split("\n");
    let html = "";
    let inList = false;
    const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };

    for (const raw of lines) {
      const line = raw.trim();
      if (!line) { closeList(); continue; }
      const m = line.match(/^[-•*]\s+(.*)/) || line.match(/^\d+[.)]\s+(.*)/);
      if (m) {
        if (!inList) { html += "<ul>"; inList = true; }
        html += `<li>${m[1]}</li>`;
      } else {
        closeList();
        html += `<p>${line}</p>`;
      }
    }
    closeList();
    return html || "<p></p>";
  }

  function scrollToBottom() {
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  // ----------------------- Thêm message vào khung -----------------------

  function addMessage(role) {
    if (welcomeEl && welcomeEl.parentNode) welcomeEl.remove();

    const msg = document.createElement("div");
    msg.className = `msg ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "🧑" : "🎓";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    msg.append(avatar, bubble);
    chatEl.appendChild(msg);
    scrollToBottom();
    return bubble;
  }

  function showTyping(bubble) {
    bubble.innerHTML =
      '<div class="typing"><span></span><span></span><span></span></div>';
  }

  // ----------------------- Gọi API (streaming) -----------------------

  async function sendMessage(text) {
    if (busy || !text.trim()) return;
    busy = true;
    sendBtn.disabled = true;

    // 1) Hiển thị message người dùng
    const userBubble = addMessage("user");
    userBubble.textContent = text;
    history.push({ role: "user", content: text });

    // 2) Bong bóng bot + typing
    const botBubble = addMessage("bot");
    showTyping(botBubble);

    let answer = "";
    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });
      if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        answer += decoder.decode(value, { stream: true });
        botBubble.innerHTML = formatMessage(answer);
        scrollToBottom();
      }
      answer += decoder.decode();
      if (answer.trim()) {
        botBubble.innerHTML = formatMessage(answer);
        history.push({ role: "assistant", content: answer });
      } else {
        botBubble.innerHTML = formatMessage("Xin lỗi, mình chưa nhận được phản hồi. Bạn thử lại nhé!");
      }
    } catch (err) {
      console.error(err);
      botBubble.innerHTML = formatMessage(
        "⚠️ Có lỗi kết nối khi xử lý câu hỏi. Bạn vui lòng thử lại sau ít phút nhé!"
      );
    } finally {
      busy = false;
      sendBtn.disabled = false;
      inputEl.focus();
      scrollToBottom();
    }
  }

  // ----------------------- Sự kiện UI -----------------------

  function autoGrow() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + "px";
  }

  formEl.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = "";
    autoGrow();
    sendMessage(text);
  });

  inputEl.addEventListener("input", autoGrow);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      formEl.requestSubmit();
    }
  });

  resetBtn.addEventListener("click", () => {
    if (busy) return;
    history = [];
    chatEl.innerHTML = "";
    chatEl.appendChild(welcomeEl);
    inputEl.focus();
  });

  // ----------------------- Câu hỏi gợi ý -----------------------

  async function loadSuggestions() {
    try {
      const resp = await fetch("/api/suggestions");
      const data = await resp.json();
      (data.suggestions || []).forEach((q) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = q;
        chip.addEventListener("click", () => sendMessage(q));
        suggestionsEl.appendChild(chip);
      });
    } catch (err) {
      console.error("Không tải được gợi ý:", err);
    }
  }

  loadSuggestions();
  inputEl.focus();
})();
