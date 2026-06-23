# 🎓 SBI Smart Agent

Chatbot tư vấn tuyển sinh cho chương trình **Thương mại số thông minh & Đổi mới kinh doanh**
(*Smart Digital Commerce and Business Innovation – SBI*), ngành Thương mại điện tử (mã 7340122),
**Trường Đại học Ngoại thương (FTU)**.

Trợ lý trả lời câu hỏi của học sinh/phụ huynh về chương trình học, môn học, hướng chuyên sâu,
thực hành – dự án, công nghệ, cơ hội việc làm… dựa trên bộ tri thức chính thức gồm 50 cặp hỏi-đáp.

> Slogan chương trình: *Kết nối công nghệ – Khơi nguồn đổi mới – Kiến tạo giá trị bền vững.*

---

## ✨ Tính năng

- 💬 Chat **streaming** thời gian thực, giao diện tiếng Việt, responsive (đẹp trên cả mobile).
- 🧠 **Bám sát tri thức**: trả lời dựa trên 50 Q&A; câu ngoài phạm vi → hướng dẫn liên hệ Khoa QTKD – FTU.
- ⚡ **Prompt caching** của Claude: nạp toàn bộ tri thức vào ngữ cảnh nhưng vẫn rẻ & nhanh.
- ✨ **Gợi ý câu hỏi** theo nhóm chủ đề, giữ ngữ cảnh hội thoại nhiều lượt.
- 📞 **Đăng ký tư vấn (lead capture)**: thu thập thông tin khách quan tâm, lưu vào Cloud Logging và (tuỳ chọn) Google Sheet.
- 🛠️ **Trang quản trị `/admin`**: xem lead, thêm/sửa/xoá Q&A, **nạp Claude API key & chọn model** — tất cả ngay trên web, không cần deploy lại.
- 💾 **Lưu trữ bền vững (Firestore)**: lead & Q&A không mất khi Cloud Run tái tạo instance (tự fallback file khi chạy local).
- 🧪 **Demo mode**: chạy được ngay cả khi chưa có API key (truy hồi câu trả lời từ dataset).

## 🏗️ Kiến trúc

```
Trình duyệt ──► Frontend (HTML/CSS/JS) ──► FastAPI (/api/chat, streaming)
                                              │  • Nạp 50 Q&A → system prompt (prompt caching)
                                              ▼
                                          Claude API (Anthropic)
                                              │
                                              ▼
                                     Google Cloud Run (Docker)
```

| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.11 · FastAPI · Uvicorn |
| LLM | Claude API (`anthropic` SDK) · streaming · prompt caching |
| Frontend | HTML + CSS + Vanilla JS (không framework) |
| Triển khai | Docker → Google Cloud Run |

## 📁 Cấu trúc thư mục

```
SBI-Smart-Agent/
├── app/
│   ├── main.py          # FastAPI: /, /admin, /api/chat, /api/lead, /api/admin/*
│   ├── config.py        # Cấu hình từ biến môi trường
│   ├── llm.py           # Client Claude (streaming + caching) + demo mode
│   ├── knowledge.py     # Nạp & merge Q&A (gốc + admin) → system prompt
│   ├── leads.py         # Lưu lead (log + Google Sheet + store)
│   ├── store.py         # Lưu trữ: Firestore hoặc file (tự fallback)
│   └── static/          # index.html, app.js, style.css + admin.html/js/css
├── data/
│   ├── sbi_qa_dataset.jsonl   # 50 Q&A gốc (knowledge base)
│   ├── sbi_qa_chat.jsonl      # Định dạng chat (để fine-tune sau)
│   ├── system_prompt.txt      # System prompt vai trò chatbot
│   └── build_dataset.py       # Script tái tạo dataset
├── tests/test_api.py    # Test (chạy demo mode, không cần mạng)
├── Dockerfile · deploy.sh · requirements.txt · .env.example
└── .github/workflows/deploy.yml   # (Tuỳ chọn) CI/CD tự động deploy
```

## 🚀 Chạy thử ở máy (local)

```bash
# 1) Cài đặt
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 2) (Tuỳ chọn) cấu hình API key để dùng Claude thật
cp .env.example .env
#   rồi mở .env, điền ANTHROPIC_API_KEY=sk-ant-...
#   (Nếu bỏ trống, app vẫn chạy ở "demo mode")

# 3) Khởi động
uvicorn app.main:app --reload --port 8080
```

Mở trình duyệt: <http://localhost:8080>

Chạy test:

```bash
pytest -v
```

## ☁️ Triển khai lên Google Cloud Run

> Thực hiện trên **Google Cloud Shell** (đã có sẵn `gcloud`) hoặc máy đã cài Google Cloud SDK.

```bash
# 1) Lấy mã nguồn
git clone https://github.com/thoannv1976/SBI-Smart-Agent.git
cd SBI-Smart-Agent

# 2) Đặt API key Claude (sẽ được lưu an toàn vào Secret Manager)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3) (Tuỳ chọn) đổi project/region nếu cần
export PROJECT_ID="sbi-smart-agent"
export REGION="asia-southeast1"

# 4) Deploy
chmod +x deploy.sh
./deploy.sh
```

Script sẽ tự động: bật API cần thiết → lưu API key vào **Secret Manager** → build từ `Dockerfile`
qua **Cloud Build** → deploy lên **Cloud Run** và in ra URL dịch vụ.

### Cấu hình (biến môi trường)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(trống)* | API key Claude. Trống → demo mode. |
| `SBI_MODEL` | `claude-sonnet-4-6` | Model Claude. Đổi `claude-haiku-4-5-20251001` để rẻ/nhanh hơn. |
| `SBI_MAX_TOKENS` | `1024` | Độ dài tối đa câu trả lời. |
| `SBI_TEMPERATURE` | `0.2` | Độ "sáng tạo" (thấp = bám dữ liệu). |
| `SBI_MAX_HISTORY_TURNS` | `12` | Số lượt hội thoại giữ làm ngữ cảnh. |
| `SBI_LEADS_WEBHOOK_URL` | *(trống)* | (Tuỳ chọn) URL Google Apps Script để ghi lead vào Google Sheet. |
| `SBI_ADMIN_TOKEN` | *(trống)* | Token bảo vệ `/admin`. Trống → trang quản trị bị tắt. |
| `SBI_USE_FIRESTORE` | `auto` | `auto`/`1`/`0` — dùng Firestore hay file cục bộ. |
| `SBI_FIRESTORE_PROJECT` | *(trống)* | Project GCP chứa Firestore (Cloud Run đặt sẵn trong `deploy.sh`). |
| `SBI_USE_SECRET_MANAGER` | `auto` | Cho phép nạp API key từ `/admin` (lưu Secret Manager). |
| `SBI_GCP_PROJECT` | *(trống)* | Project GCP cho Secret Manager (`deploy.sh` đặt sẵn). |
| `SBI_API_KEY_SECRET` | `anthropic-api-key` | Tên secret chứa Claude API key. |
| `PORT` | `8080` | Cổng server (Cloud Run tự cấp). |

## 🔁 Cập nhật dữ liệu Q&A

Sửa nội dung trong `data/build_dataset.py` rồi chạy lại để sinh lại JSONL:

```bash
cd data && python build_dataset.py
```

## 📞 Lead capture (Đăng ký tư vấn)

Khi khách bấm **"Đăng ký tư vấn"** và gửi form, lead được lưu theo 3 lớp:

1. **Cloud Logging** (luôn bật): in một dòng JSON `{"event":"lead", ...}` ra stdout.
   Trên Cloud Run, lọc lead bằng truy vấn: `jsonPayload.event="lead"`.
2. **Google Sheet** (tuỳ chọn): đặt biến `SBI_LEADS_WEBHOOK_URL` trỏ tới một
   Google Apps Script Web App để tự ghi vào Sheet (xem dưới).
3. **File cục bộ** `data/leads.jsonl` (chỉ cho local dev; Cloud Run sẽ mất khi
   instance tái tạo — đừng phụ thuộc vào lớp này trên production).

### Nối Google Sheet trong 4 bước

1. Tạo Google Sheet mới, vào **Extensions → Apps Script**, dán đoạn sau:

   ```javascript
   function doPost(e) {
     const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
     const d = JSON.parse(e.postData.contents);
     sheet.appendRow([d.created_at, d.name, d.phone, d.email, d.note, d.source]);
     return ContentService.createTextOutput("ok");
   }
   ```

2. **Deploy → New deployment → Web app**, chọn *Execute as: Me*,
   *Who has access: Anyone*. Copy URL Web App.
3. Đặt biến môi trường khi deploy:
   `gcloud run services update sbi-smart-agent --region asia-southeast1 --set-env-vars "SBI_LEADS_WEBHOOK_URL=<URL>"`
   (hoặc thêm vào `deploy.sh`).
4. Xong — mỗi lead mới sẽ tự xuất hiện thành một dòng trong Google Sheet.

## 🛠️ Trang quản trị (`/admin`)

Truy cập `https://<service-url>/admin`, đăng nhập bằng `SBI_ADMIN_TOKEN`. Tại đây:

- **Kho tri thức (Q&A)**: thêm / sửa / xoá câu hỏi-đáp. Thay đổi áp dụng **ngay**
  cho chatbot (system prompt được dựng lại), không cần deploy lại. Mỗi mục có nhãn
  *Gốc / Đã sửa / Tự thêm* để dễ theo dõi.
- **Đăng ký tư vấn**: xem danh sách lead, gọi/email nhanh, **xuất CSV**.
- **Cấu hình**: nạp/đổi **Claude API key** (ghi vào Secret Manager, *có hiệu lực ngay*
  không cần deploy lại), chọn **model**, chỉnh `max_tokens`/`temperature`, và **kiểm
  tra kết nối**. API không bao giờ trả về key đầy đủ (chỉ hiển thị che `sk-ant…wxyz`).

> Bảo mật: để trống `SBI_ADMIN_TOKEN` thì toàn bộ `/api/admin/*` trả về 503 (tắt).
> Hãy đặt token đủ mạnh khi bật.

## 💾 Lưu trữ bền vững (Firestore)

Cloud Run là **stateless** — file ghi xuống sẽ mất khi instance tái tạo. Vì vậy
lead và Q&A chỉnh-sửa được lưu vào **Firestore** để bền vững và dùng chung giữa
các instance. Cơ chế chọn kho lưu trữ (`SBI_USE_FIRESTORE`):

- `auto` (mặc định): dùng Firestore nếu có `SBI_FIRESTORE_PROJECT` + thư viện;
  ngược lại tự dùng **file cục bộ** (tiện cho chạy local).
- `1` / `0`: ép bật / tắt Firestore.

`deploy.sh` (mặc định `USE_FIRESTORE=1`) sẽ tự **bật Firestore API**, **tạo
database** và **cấp quyền** cho service account của Cloud Run. Nếu muốn dùng file
thay vì Firestore: `USE_FIRESTORE=0 ./deploy.sh`.

> 🔑 **API key** được lưu riêng trong **Secret Manager** (không phải Firestore) cho
> an toàn. `deploy.sh` tự tạo secret + cấp quyền đọc/ghi cho Cloud Run, nên bạn có
> thể **nạp key trực tiếp ở trang `/admin`** mà không cần dùng dòng lệnh.

## 🔌 API

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/` | Giao diện chat |
| `POST` | `/api/chat` | Body `{"messages":[{"role","content"}]}` → trả lời streaming (text/plain) |
| `POST` | `/api/lead` | Đăng ký tư vấn. Body `{"name","phone","email","note","context"}` |
| `GET` | `/api/suggestions` | Danh sách câu hỏi gợi ý |
| `GET` | `/healthz` | Health check |
| `GET` | `/admin` | Trang quản trị (cần `SBI_ADMIN_TOKEN`) |
| `*` | `/api/admin/*` | API quản trị lead & Q&A (header `X-Admin-Token`) |

---

*Thông tin do chatbot cung cấp mang tính tham khảo. Vui lòng liên hệ Khoa Quản trị Kinh doanh –
Trường Đại học Ngoại thương để được tư vấn chính thức.*
