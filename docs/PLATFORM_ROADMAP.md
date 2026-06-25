# 🌐 Kế hoạch nâng cấp SBI thành Hệ sinh thái (Platform)

> Từ một **chatbot tư vấn** → một **cổng (platform) trung tâm** cho chương trình
> **Thương mại số thông minh & Đổi mới kinh doanh (SBI)** — Trường ĐH Ngoại thương.
> Mục tiêu: *site key nhất* về đào tạo **Thương mại số thông minh · Kinh doanh thông
> minh · Kinh doanh số**; thu hút thí sinh, đồng hành sinh viên suốt 4 năm và kết
> nối cựu sinh viên.

---

## 1. Tầm nhìn & nguyên tắc

**Tầm nhìn:** SBI Platform là "cổng một cửa" (one-stop hub) kết nối toàn bộ công
cụ hỗ trợ triển khai chương trình SBI, đồng thời là kênh truyền thông – tuyển sinh –
gắn kết người học chính thức của chương trình.

**Nguyên tắc thiết kế:**
1. **Hub-and-spoke** — cổng trung tâm (app này) không ôm hết mọi thứ; các app
   chuyên biệt (LMS, công cụ OBE, trắc nghiệm nghề nghiệp…) là "vệ tinh", kết nối
   qua link → nhúng (embed) → API → đăng nhập một lần (SSO), tăng dần độ sâu.
2. **Config-driven** — mọi đường link, video, khóa học nổi bật… quản lý trong
   `/admin`, đổi được mà **không cần deploy lại** (tận dụng Firestore + Secret
   Manager đã có).
3. **Một danh tính, nhiều chặng** — cùng một người dùng đi qua các vai: *thí sinh →
   sinh viên năm 1–4 → cựu sinh viên*, platform phục vụ đúng nhu cầu từng chặng.
4. **Mobile-first & SEO** — phần lớn truy cập từ điện thoại; nội dung phải chuẩn SEO
   để trở thành "site key" của lĩnh vực.

---

## 2. Đối tượng & vòng đời người dùng (4 năm + sau tốt nghiệp)

| Chặng | Đối tượng | Nhu cầu chính | Platform phục vụ |
|---|---|---|---|
| **Awareness** | Thí sinh, phụ huynh | Hiểu ngành, học phí, cơ hội | Landing, chatbot, video, đăng ký tư vấn, trắc nghiệm nghề |
| **Onboarding** | Tân sinh viên | Nhập học, định hướng | Cẩm nang, LMS, lịch học, cộng đồng |
| **Engagement** | SV năm 1–4 | Học liệu, dự án, sự kiện, thực tập | LMS, OBE, tài nguyên, job/intern board |
| **Retention** | SV các năm | Động lực, kết nối, thành tích | Dashboard cá nhân, thông báo, cộng đồng |
| **Alumni** | Cựu SV | Mạng lưới, việc làm, mentor | Alumni network, job board, mentorship |

---

## 3. Kiến trúc tổng thể (Hub-and-Spoke)

```
                         ┌──────────────────────────────┐
                         │        SBI PLATFORM (HUB)      │
   Thí sinh ─┐           │  • Trang chủ / cổng portal     │
   Sinh viên ─┼──► Web ─►│  • Chatbot (đã có)             │
   Cựu SV ───┘   /Mobile │  • Lead & CRM nhẹ (đã có)      │
                         │  • Thống kê (đã có)            │
                         │  • Identity / SSO (Phase 3)    │
                         │  • Trung tâm tích hợp (config) │
                         └───────┬───────┬───────┬────────┘
        link / embed / API / SSO │       │       │
        ┌──────────┬─────────────┼───────┼───────┼─────────────┐
        ▼          ▼             ▼       ▼       ▼             ▼
   ┌─────────┐ ┌────────┐  ┌──────────┐ ┌──────────┐ ┌──────────────┐
   │ YouTube │ │  LMS   │  │ Công cụ  │ │ Trắc     │ │ Sự kiện/Blog │
   │ (video) │ │(khóa h)│  │ OBE/g.án │ │ nghiệm   │ │ /Tài nguyên  │
   └─────────┘ └────────┘  └──────────┘ └──────────┘ └──────────────┘
```

- **Hub** = repo hiện tại (FastAPI + Firestore + Secret Manager + static frontend).
- **Spokes** = app/dịch vụ riêng; hub chỉ cần biết **URL + (tuỳ chọn) API**.
- Mức độ tích hợp tăng dần: **Link** (mở tab mới) → **Embed** (nhúng iframe/cards)
  → **API** (kéo dữ liệu: video, khóa học, kết quả test) → **SSO** (1 lần đăng nhập).

---

## 4. Các module theo yêu cầu

### 4.1 YouTube — 3 video nổi bật trên trang chủ
- **Cách A (đơn giản, khuyên dùng để khởi động):** admin dán **3 video ID** (hoặc
  link) trong `/admin` → trang chủ nhúng player. Không cần API key, không lo quota.
- **Cách B (tự động):** lưu **Channel ID + YouTube Data API key** (Secret Manager) →
  backend gọi API lấy 3 video **xem nhiều nhất / mới nhất**, cache vài giờ.
- Hiển thị: 1 video lớn + 2 video nhỏ, hoặc carousel; kèm link "Xem kênh".

### 4.2 LMS — link + khóa học hot nhất
- Nút lớn **"Vào LMS"** (Moodle/Google Classroom/khác — chỉ cần URL).
- Mục **"Khóa học nổi bật"**: thẻ khóa học (ảnh, tên, mô tả ngắn, link) do admin
  quản lý. Giai đoạn sau: kéo tự động qua **LMS API** (Moodle có REST API) nếu cần.

### 4.3 Chatbot (✅ đã có — tái sử dụng)
- FAQ theo lượt hỏi · câu hỏi thường gặp + số lượt · gợi ý 3 câu hỏi liên quan.
- Trên platform: nhúng dưới dạng **widget bong bóng** ở mọi trang + 1 trang chat đầy đủ.

### 4.4 Công cụ tạo giáo trình / tài liệu OBE — link
- Thẻ/nút dẫn tới app tạo **giáo trình & tài liệu OBE** (đối tượng: giảng viên).
- Có thể đặt sau khu vực "Dành cho giảng viên" (phân quyền ở Phase 3).

### 4.5 App trắc nghiệm nghề nghiệp — link
- Thẻ kêu gọi **"Khám phá bạn hợp ngành nào?"** dẫn tới app trắc nghiệm.
- Giai đoạn sau: nhận **kết quả test** qua API → cá nhân hóa tư vấn của chatbot.

### 4.6 Trung tâm tích hợp (Integration Hub) — admin quản lý
- Tab mới trong `/admin`: nhập **link & cấu hình** cho mọi vệ tinh (YouTube, LMS,
  OBE, trắc nghiệm, mạng xã hội…). Lưu vào Firestore → đổi tức thì, không deploy.

---

## 5. Lộ trình theo giai đoạn

| Phase | Tên | Nội dung chính | Ước lượng |
|---|---|---|---|
| **0** | Nền tảng (✅ xong) | Chatbot, tri thức, lead, admin, Firestore, Secret Manager, thống kê | Đã có |
| **1** | **Cổng portal** | Trang chủ dạng hub: hero + tuyển sinh CTA, YouTube top 3, khóa học nổi bật, lối vào chatbot, thẻ liên kết OBE/trắc nghiệm, lead. Trung tâm tích hợp trong /admin | ~1–2 tuần |
| **2** | Nội dung & SEO | Tin tức/sự kiện/blog, thư viện tài nguyên, trang ngành chuẩn SEO, sitemap, OpenGraph, hiệu năng | ~2–3 tuần |
| **3** | Danh tính & vòng đời SV | Đăng nhập (Google/SSO), hồ sơ & vai trò (thí sinh/SV/alumni), dashboard cá nhân, thông báo | ~3–4 tuần |
| **4** | Tích hợp sâu + SSO | API LMS (tiến độ học), kết quả trắc nghiệm → gợi ý, SSO chung các app vệ tinh | ~3–4 tuần |
| **5** | Cộng đồng & Alumni | Diễn đàn/hỏi đáp, job & internship board, mentorship, mạng lưới cựu SV | ~3–4 tuần |

> Các phase chạy nối tiếp nhưng **độc lập** — có thể dừng/đổi thứ tự theo ưu tiên.
> Phase 1 đem lại giá trị "cổng" thấy ngay; Phase 3 là bước ngoặt giữ chân 4 năm.

---

## 6. Quyết định công nghệ

| Hạng mục | Khuyến nghị | Ghi chú |
|---|---|---|
| Backend | Giữ **FastAPI** | Đã có; phục vụ portal + API + proxy tích hợp |
| Frontend Phase 1 | **Nâng cấp static hiện tại** (HTML/CSS/JS) | Ship nhanh, ít rủi ro |
| Frontend Phase 2+ | Cân nhắc **Astro** (hoặc Next.js) | SSR/SSG cho SEO mạnh — quan trọng với "site key" |
| Auth (Phase 3) | **Firebase Auth / Google Identity** | Hợp với Firestore; hỗ trợ Google Workspace của trường |
| Dữ liệu | **Firestore** (đã có) | + Cloud Storage cho ảnh/tài liệu |
| Secrets | **Secret Manager** (đã có) | YouTube API key, LMS token… |
| Cấu hình tích hợp | **Firestore config + /admin** (đã có pattern) | Đổi link không cần deploy |
| Hạ tầng | **Cloud Run + Docker** (đã có) | + CDN/cache cho video & ảnh |

---

## 7. Mô hình dữ liệu (mở rộng dần)

- **`config/app`** (đã có) → thêm: `youtube_channel_id`, `youtube_video_ids[]`,
  `lms_url`, `obe_url`, `career_test_url`, `social{}`, `featured_courses[]`.
- **`courses`** — khóa học nổi bật (title, desc, thumbnail, url, order).
- **`videos_cache`** — cache kết quả YouTube API (nếu dùng Cách B).
- **`posts`** (Phase 2) — tin tức/sự kiện/blog.
- **`users`, `profiles`, `roles`** (Phase 3) — danh tính & vòng đời.
- **`enrollments`, `test_results`** (Phase 4) — tích hợp LMS & trắc nghiệm.

---

## 8. Bảo mật, vận hành, đo lường

- **Phân quyền**: công khai (thí sinh) · SV (đăng nhập) · giảng viên (OBE) · admin.
- **Bảo mật**: token/secret trong Secret Manager; HTTPS; rate-limit API công khai.
- **KPI gợi ý**: lượt truy cập & nguồn, số lead/tuần, tỉ lệ xem video, click sang
  LMS, số câu hỏi chatbot, tỉ lệ SV quay lại (retention), số alumni kết nối.
- **Phân tích**: mở rộng tab Thống kê (đã có) + GA4/Looker Studio.

---

## 9. Bắt đầu ngay — đặc tả Phase 1 (Cổng portal)

**Trang chủ mới** (thay layout chat toàn màn hình hiện tại) gồm các khối:
1. **Hero**: tên chương trình + slogan + 2 CTA ("Đăng ký tư vấn", "Tìm hiểu ngành").
2. **Về SBI**: 3–4 điểm nổi bật (mã ngành 7340122, 131 tín chỉ, hướng chuyên sâu…).
3. **Video** (YouTube top 3).
4. **Khóa học nổi bật** + nút "Vào LMS".
5. **Hệ sinh thái công cụ**: thẻ liên kết → Trắc nghiệm nghề nghiệp, Công cụ OBE, …
6. **Chatbot**: widget bong bóng nổi ở mọi nơi + lối vào trang chat.
7. **Đăng ký tư vấn** (form đã có) + chân trang (liên hệ, mạng xã hội).
8. **`/admin` → tab "Tích hợp"**: quản lý toàn bộ link/video/khóa học ở trên.

**Cần bạn cung cấp để triển khai Phase 1:**
- 🔗 Link **kênh YouTube** (+ 3 video muốn hiển thị, hoặc để tự lấy top theo lượt xem).
- 🔗 URL **LMS** + danh sách **khóa học hot** (tên + link + ảnh nếu có).
- 🔗 URL **app trắc nghiệm nghề nghiệp** và **công cụ tạo giáo trình/OBE**.
- 🔗 Link **mạng xã hội** (Fanpage, TikTok…) nếu muốn đưa vào chân trang.

> Thiếu link nào, tôi vẫn dựng được khung (dùng placeholder + bật/tắt trong /admin),
> bạn điền sau là chạy ngay.
