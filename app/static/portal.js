"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    (s || "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  $("year").textContent = new Date().getFullYear();

  // ----------------------- Chatbot widget -----------------------
  const fab = $("chatFab");
  const widget = $("chatWidget");
  const frame = $("chatFrame");
  let frameLoaded = false;

  function openChat() {
    if (!frameLoaded) {
      frame.src = "/chat";
      frameLoaded = true;
    }
    widget.hidden = false;
    fab.textContent = "✕";
  }
  function closeChat() {
    widget.hidden = true;
    fab.textContent = "💬";
  }
  fab.addEventListener("click", () => (widget.hidden ? openChat() : closeChat()));
  $("chatWidgetClose").addEventListener("click", closeChat);
  $("heroChatBtn").addEventListener("click", openChat);

  // ----------------------- Nạp cấu hình cổng -----------------------
  function videoId(s) {
    const m = String(s).match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([\w-]{11})/);
    return m ? m[1] : String(s).trim();
  }

  async function loadPortal() {
    let cfg = {};
    try {
      cfg = await (await fetch("/api/portal")).json();
    } catch (e) {
      return;
    }

    if (cfg.hero_title) $("heroTitle").textContent = cfg.hero_title;
    if (cfg.hero_subtitle) $("heroSubtitle").textContent = cfg.hero_subtitle;

    // Video YouTube
    const vids = (cfg.youtube_video_ids || []).map(videoId).filter(Boolean).slice(0, 3);
    if (vids.length) {
      $("videoGrid").innerHTML = vids
        .map(
          (id) =>
            `<div class="video-embed"><iframe src="https://www.youtube.com/embed/${encodeURIComponent(id)}" title="YouTube video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>`
        )
        .join("");
      $("video").hidden = false;
    }
    if (cfg.youtube_channel_url) {
      const cl = $("channelLink");
      cl.href = cfg.youtube_channel_url;
      cl.hidden = false;
    }

    // Khóa học nổi bật
    const courses = (cfg.featured_courses || []).filter((c) => c && (c.title || c.url));
    if (courses.length) {
      $("courseGrid").innerHTML = courses
        .map((c) => {
          const thumb = c.thumbnail
            ? `style="background-image:url('${esc(c.thumbnail)}')"`
            : "";
          const inner = `<div class="course-thumb" ${thumb}>${c.thumbnail ? "" : "📘"}</div>
            <div class="course-body"><h3>${esc(c.title || "")}</h3><p>${esc(c.desc || "")}</p></div>`;
          return c.url
            ? `<a class="course-card" href="${esc(c.url)}" target="_blank" rel="noopener">${inner}</a>`
            : `<div class="course-card">${inner}</div>`;
        })
        .join("");
      $("khoa-hoc").hidden = false;
    }
    if (cfg.lms_url) {
      const b = $("lmsBtn");
      b.href = cfg.lms_url;
      b.hidden = false;
    }

    // Hệ sinh thái: gán link hoặc vô hiệu hóa nếu chưa cấu hình
    document.querySelectorAll(".eco-link").forEach((a) => {
      const url = cfg[a.dataset.key];
      if (url) a.href = url;
      else a.classList.add("disabled");
    });

    // Mạng xã hội (footer)
    const social = cfg.social || {};
    const labels = {
      facebook: "Facebook", tiktok: "TikTok", youtube: "YouTube",
      zalo: "Zalo", instagram: "Instagram", website: "Website",
    };
    const sl = Object.entries(social)
      .filter(([, v]) => v)
      .map(([k, v]) => `<a href="${esc(v)}" target="_blank" rel="noopener">${labels[k] || esc(k)}</a>`)
      .join("");
    $("socialLinks").innerHTML =
      sl || '<span style="color:#94a3b8;font-size:13px">Đang cập nhật…</span>';
  }
  loadPortal();

  // ----------------------- Form đăng ký tư vấn -----------------------
  const form = $("pLeadForm");
  const msg = $("pLeadMsg");
  const submit = $("pLeadSubmit");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = form.elements.name.value.trim();
    const phone = form.elements.phone.value.trim();
    msg.hidden = true;
    msg.className = "lead-msg";
    if (!name) {
      msg.textContent = "Vui lòng nhập họ và tên.";
      msg.classList.add("err");
      msg.hidden = false;
      return;
    }
    if (phone.replace(/\D/g, "").length < 8) {
      msg.textContent = "Số điện thoại không hợp lệ.";
      msg.classList.add("err");
      msg.hidden = false;
      return;
    }
    submit.disabled = true;
    submit.textContent = "Đang gửi…";
    try {
      const resp = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          phone,
          email: form.elements.email.value.trim(),
          note: form.elements.note.value.trim(),
          source: "portal",
        }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(data.detail || "Gửi không thành công");
      msg.className = "lead-msg ok";
      msg.textContent = data.message || "Cảm ơn bạn! Chúng tôi sẽ liên hệ lại sớm.";
      msg.hidden = false;
      form.reset();
    } catch (err) {
      msg.className = "lead-msg err";
      msg.textContent = "⚠️ " + err.message;
      msg.hidden = false;
    } finally {
      submit.disabled = false;
      submit.textContent = "Gửi đăng ký";
    }
  });
})();
