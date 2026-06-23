# ---- SBI Smart Agent: image production cho Google Cloud Run ----
FROM python:3.11-slim

# Không ghi .pyc, log ra thẳng stdout (hợp với Cloud Run logging)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Cài dependencies trước để tận dụng cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn & dữ liệu
COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8080

# Cloud Run truyền PORT qua biến môi trường; uvicorn lắng nghe theo PORT đó.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
