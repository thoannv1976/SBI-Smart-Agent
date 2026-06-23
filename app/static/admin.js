"use strict";
(() => {
  const TOKEN_KEY = "sbi_admin_token";
  let token = localStorage.getItem(TOKEN_KEY) || "";
  let categories = {};
  let qaItems = [];
  let leads = [];

  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    (s || "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  function headers(json) {
    const h = { "X-Admin-Token": token };
    if (json) h["Content-Type"] = "application/json";
    return h;
  }

  async function api(path, opts = {}) {
    const resp = await fetch(path, { ...opts, headers: { ...headers(opts.body ? true : false), ...(opts.headers || {}) } });
    if (resp.status === 401 || resp.status === 503) {
      const d = await resp.json().catch(() => ({}));
      throw new Error(d.detail || "Không có quyền truy cập");
    }
    return resp;
  }

  // ----------------------------- Đăng nhập -----------------------------
  const SRC_LABEL = { base: "Gốc", edited: "Đã sửa", custom: "Tự thêm" };

  async function tryLogin() {
    const r = await fetch("/api/admin/check", { headers: { "X-Admin-Token": token } });
    if (!r.ok) return false;
    const d = await r.json();
    $("storageBadge").textContent = "Lưu trữ: " + (d.storage || "?");
    return true;
  }

  function showApp() {
    $("login").hidden = true;
    $("adminApp").hidden = false;
    loadQA();
    loadLeads();
  }

  function showLogin(msg) {
    $("adminApp").hidden = true;
    $("login").hidden = false;
    if (msg) { $("loginMsg").textContent = msg; $("loginMsg").hidden = false; }
  }

  $("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    token = $("tokenInput").value.trim();
    $("loginMsg").hidden = true;
    if (!token) return;
    if (await tryLogin()) {
      localStorage.setItem(TOKEN_KEY, token);
      showApp();
    } else {
      showLogin("Token không đúng. Vui lòng thử lại.");
    }
  });

  $("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem(TOKEN_KEY);
    token = "";
    showLogin();
  });

  // ----------------------------- Tabs -----------------------------
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const t = btn.dataset.tab;
      $("tab-qa").hidden = t !== "qa";
      $("tab-leads").hidden = t !== "leads";
      $("tab-settings").hidden = t !== "settings";
      if (t === "settings") loadSettings();
    });
  });

  // ----------------------------- Q&A -----------------------------
  async function loadQA() {
    try {
      const d = await (await api("/api/admin/qa")).json();
      qaItems = d.items || [];
      categories = d.categories || {};
      renderQA();
    } catch (err) {
      showLogin(err.message);
    }
  }

  function renderQA() {
    const term = $("qaSearch").value.trim().toLowerCase();
    const list = qaItems.filter(
      (it) => !term || (it.question + " " + it.answer).toLowerCase().includes(term)
    );
    $("qaCount").textContent = `${list.length}/${qaItems.length} mục`;
    const box = $("qaList");
    if (!list.length) {
      box.innerHTML = '<div class="empty">Không có mục nào.</div>';
      return;
    }
    box.innerHTML = list
      .map(
        (it) => `
      <div class="qa-card">
        <div class="qa-card-top">
          <span class="qa-cat">${esc(it.category_label || it.category)}</span>
          <span class="qa-src ${it.source}">${SRC_LABEL[it.source] || it.source}</span>
          <span class="qa-actions">
            <button class="icon-btn" data-edit="${esc(it.id)}">✏️ Sửa</button>
            <button class="icon-btn danger" data-del="${esc(it.id)}">🗑️ Xoá</button>
          </span>
        </div>
        <div class="qa-q">${esc(it.question)}</div>
        <div class="qa-a">${esc(it.answer)}</div>
      </div>`
      )
      .join("");
    box.querySelectorAll("[data-edit]").forEach((b) =>
      b.addEventListener("click", () => openQA(b.dataset.edit))
    );
    box.querySelectorAll("[data-del]").forEach((b) =>
      b.addEventListener("click", () => delQA(b.dataset.del))
    );
  }

  $("qaSearch").addEventListener("input", renderQA);

  // --- Modal Q&A ---
  function fillCategorySelect(selected) {
    const sel = $("qaCategory");
    const entries = Object.entries(categories);
    sel.innerHTML = entries.map(([k, v]) => `<option value="${esc(k)}">${esc(v)}</option>`).join("");
    if (selected && !categories[selected]) {
      sel.innerHTML += `<option value="${esc(selected)}">${esc(selected)}</option>`;
    }
    if (selected) sel.value = selected;
  }

  function openQA(id) {
    const f = $("qaForm");
    $("qaMsg").hidden = true;
    const item = qaItems.find((x) => x.id === id);
    $("qaModalTitle").textContent = item ? "Sửa Q&A" : "Thêm Q&A";
    f.elements.id.value = item ? item.id : "";
    fillCategorySelect(item ? item.category : "tuyen_sinh");
    f.elements.question.value = item ? item.question : "";
    f.elements.answer.value = item ? item.answer : "";
    $("qaModal").hidden = false;
    f.elements.question.focus();
  }

  function closeQA() { $("qaModal").hidden = true; }
  $("qaAddBtn").addEventListener("click", () => openQA(null));
  $("qaClose").addEventListener("click", closeQA);
  $("qaModal").addEventListener("click", (e) => { if (e.target === $("qaModal")) closeQA(); });

  $("qaForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target;
    const payload = {
      id: f.elements.id.value,
      category: f.elements.category.value,
      question: f.elements.question.value.trim(),
      answer: f.elements.answer.value.trim(),
    };
    $("qaMsg").hidden = true;
    if (!payload.question || !payload.answer) {
      $("qaMsg").className = "lead-msg err";
      $("qaMsg").textContent = "Cần nhập cả câu hỏi và câu trả lời.";
      $("qaMsg").hidden = false;
      return;
    }
    $("qaSave").disabled = true;
    try {
      const r = await api("/api/admin/qa", { method: "POST", body: JSON.stringify(payload) });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || "Lưu thất bại");
      }
      closeQA();
      await loadQA();
    } catch (err) {
      $("qaMsg").className = "lead-msg err";
      $("qaMsg").textContent = "⚠️ " + err.message;
      $("qaMsg").hidden = false;
    } finally {
      $("qaSave").disabled = false;
    }
  });

  async function delQA(id) {
    if (!confirm("Xoá/ẩn mục này khỏi kho tri thức?")) return;
    try {
      await api(`/api/admin/qa/${encodeURIComponent(id)}`, { method: "DELETE" });
      await loadQA();
    } catch (err) {
      alert(err.message);
    }
  }

  // ----------------------------- Leads -----------------------------
  async function loadLeads() {
    try {
      const d = await (await api("/api/admin/leads")).json();
      leads = d.leads || [];
      renderLeads();
    } catch (err) {
      /* tab Q&A đã xử lý lỗi đăng nhập */
    }
  }

  function fmtTime(s) { return (s || "").replace("T", " ").replace(/\+.*$/, ""); }

  function renderLeads() {
    $("leadsCount").textContent = `${leads.length} đăng ký`;
    const wrap = $("leadsTableWrap");
    if (!leads.length) {
      wrap.innerHTML = '<div class="empty">Chưa có đăng ký tư vấn nào.</div>';
      return;
    }
    const rows = leads
      .map(
        (l) => `
      <tr>
        <td>${esc(fmtTime(l.created_at))}</td>
        <td>${esc(l.name)}</td>
        <td><a href="tel:${esc(l.phone)}">${esc(l.phone)}</a></td>
        <td>${l.email ? `<a href="mailto:${esc(l.email)}">${esc(l.email)}</a>` : ""}</td>
        <td>${esc(l.note)}</td>
      </tr>`
      )
      .join("");
    wrap.innerHTML = `<table class="leads"><thead><tr>
      <th>Thời gian</th><th>Họ tên</th><th>Điện thoại</th><th>Email</th><th>Nội dung</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
  }

  $("leadsRefresh").addEventListener("click", loadLeads);
  $("leadsCsv").addEventListener("click", () => {
    if (!leads.length) return;
    const head = ["created_at", "name", "phone", "email", "note", "source"];
    const cell = (v) => `"${String(v == null ? "" : v).replace(/"/g, '""')}"`;
    const csv = [head.join(",")]
      .concat(leads.map((l) => head.map((k) => cell(l[k])).join(",")))
      .join("\r\n");
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "sbi-leads.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  });

  // ----------------------------- Cấu hình -----------------------------
  function fillModels(models, selected) {
    const sel = $("setModel");
    const list = models || [];
    sel.innerHTML = list.map((m) => `<option value="${esc(m)}">${esc(m)}</option>`).join("");
    if (selected && !list.includes(selected)) {
      sel.innerHTML += `<option value="${esc(selected)}">${esc(selected)}</option>`;
    }
    if (selected) sel.value = selected;
  }

  async function loadSettings() {
    try {
      const d = await (await api("/api/admin/settings")).json();
      const k = d.api_key || {};
      $("keyStatus").innerHTML = k.configured
        ? `Đã cấu hình: <b>${esc(k.masked)}</b> <span class="muted">(nguồn: ${esc(k.source)})</span>`
        : "Chưa cấu hình API key — chatbot đang chạy ở chế độ <b>demo</b>.";
      const warn = $("smWarn");
      if (!k.secret_manager_available) {
        warn.hidden = false;
        warn.textContent =
          "⚠️ Secret Manager chưa sẵn sàng ở môi trường này — nhập key trên web sẽ KHÔNG lưu được. " +
          "Hãy đặt qua biến môi trường ANTHROPIC_API_KEY, hoặc deploy trên Cloud Run (deploy.sh đã bật Secret Manager).";
      } else {
        warn.hidden = true;
      }
      fillModels(d.available_models, d.model);
      $("setMaxTokens").value = d.max_tokens;
      $("setTemp").value = d.temperature;
      $("setApiKey").value = "";
    } catch (err) {
      showLogin(err.message);
    }
  }

  async function saveSettings() {
    const payload = {
      api_key: $("setApiKey").value.trim(),
      model: $("setModel").value,
      max_tokens: parseInt($("setMaxTokens").value, 10),
      temperature: parseFloat($("setTemp").value),
    };
    const msg = $("settingsMsg");
    msg.hidden = true;
    $("saveSettings").disabled = true;
    try {
      const r = await api("/api/admin/settings", { method: "POST", body: JSON.stringify(payload) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "Lưu thất bại");
      msg.className = "lead-msg ok";
      msg.textContent = "✓ Đã lưu cấu hình.";
      msg.hidden = false;
      loadSettings();
    } catch (err) {
      msg.className = "lead-msg err";
      msg.textContent = "⚠️ " + err.message;
      msg.hidden = false;
    } finally {
      $("saveSettings").disabled = false;
    }
  }

  async function testConn() {
    const msg = $("settingsMsg");
    msg.hidden = false;
    msg.className = "lead-msg";
    msg.textContent = "Đang kiểm tra…";
    $("testConn").disabled = true;
    try {
      const d = await (await api("/api/admin/settings/test", { method: "POST", body: "{}" })).json();
      msg.className = "lead-msg " + (d.ok ? "ok" : "err");
      msg.textContent = (d.ok ? "✓ " : "⚠️ ") + d.message;
    } catch (err) {
      msg.className = "lead-msg err";
      msg.textContent = "⚠️ " + err.message;
    } finally {
      $("testConn").disabled = false;
    }
  }

  $("saveSettings").addEventListener("click", saveSettings);
  $("testConn").addEventListener("click", testConn);

  // ----------------------------- Khởi động -----------------------------
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("qaModal").hidden) closeQA();
  });

  (async () => {
    if (token && (await tryLogin())) showApp();
    else showLogin();
  })();
})();
