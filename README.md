# 🎓 SBI Smart Agent

Chatbot tư vấn tuyển sinh cho chương trình **Thương mại số thông minh & Đổi mới kinh doanh**
(*Smart Digital Commerce and Business Innovation – SBI*), ngành Thương mại điện tử (mã 7340122),
**Trường Đại học Ngoại thương (FTU)**.

Trợ lý trả lời câu hỏi của học sinh/phụ huynh về chương trình học, môn học, hướng chuyên sâu,
thực hành – dự án, công nghệ, cơ hội việc làm… dựa trên bộ tri thức chính thức gồm 43 cặp hỏi-đáp.

> Slogan chương trình: *Kết nối công nghệ – Khơi nguồn đổi mới – Kiến tạo giá trị bền vững.*

---

## ✨ Tính năng

- 💬 Chat **streaming** thời gian thực, giao diện tiếng Việt, responsive (đẹp trên cả mobile).
- 🧠 **Bám sát tri thức**: trả lời dựa trên 43 Q&A; câu ngoài phạm vi → hướng dẫn liên hệ Khoa QTKD – FTU.
- ⚡ **Prompt caching** của Claude: nạp toàn bộ tri thức vào ngữ cảnh nhưng vẫn rẻ & nhanh.
- ✨ **Gợi ý câu hỏi** theo nhóm chủ đề, giữ ngữ cảnh hội thoại nhiều lượt.
- 🧪 **Demo mode**: chạy được ngay cả khi chưa có API key (truy hồi câu trả lời từ dataset).

## 🏗️ Kiến trúc

```
Trình duyệt ──► Frontend (HTML/CSS/JS) ──► FastAPI (/api/chat, streaming)
                                              │  • Nạp 43 Q&A → system prompt (prompt caching)
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
│   ├── main.py          # FastAPI: /, /api/chat, /api/suggestions, /healthz
│   ├── config.py        # Cấu hình từ biến môi trường
│   ├── llm.py           # Client Claude (streaming + caching) + demo mode
│   ├── knowledge.py     # Nạp Q&A → system prompt
│   └── static/          # index.html, style.css, app.js
├── data/
│   ├── sbi_qa_dataset.jsonl   # 43 Q&A (knowledge base)
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
| `PORT` | `8080` | Cổng server (Cloud Run tự cấp). |

## 🔁 Cập nhật dữ liệu Q&A

Sửa nội dung trong `data/build_dataset.py` rồi chạy lại để sinh lại JSONL:

```bash
cd data && python build_dataset.py
```

## 🔌 API

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/` | Giao diện chat |
| `POST` | `/api/chat` | Body `{"messages":[{"role","content"}]}` → trả lời streaming (text/plain) |
| `GET` | `/api/suggestions` | Danh sách câu hỏi gợi ý |
| `GET` | `/healthz` | Health check |

---

*Thông tin do chatbot cung cấp mang tính tham khảo. Vui lòng liên hệ Khoa Quản trị Kinh doanh –
Trường Đại học Ngoại thương để được tư vấn chính thức.*
