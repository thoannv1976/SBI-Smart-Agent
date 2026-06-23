#!/usr/bin/env bash
#
# Deploy SBI Smart Agent lên Google Cloud Run.
#
# Cách dùng (chạy trên Google Cloud Shell hoặc máy đã cài gcloud):
#   export ANTHROPIC_API_KEY="sk-ant-..."   # API key Claude của bạn
#   ./deploy.sh
#
# Có thể tuỳ chỉnh qua biến môi trường:
#   PROJECT_ID      (mặc định: sbi-smart-agent)
#   REGION          (mặc định: asia-southeast1 - Singapore)
#   SERVICE         (mặc định: sbi-smart-agent)
#   SBI_MODEL       (mặc định: claude-sonnet-4-6)
#   SBI_ADMIN_TOKEN (tuỳ chọn: bật trang /admin)
#   USE_FIRESTORE   (mặc định: 1 - tạo & dùng Firestore cho lead/Q&A bền vững)
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-sbi-smart-agent}"
REGION="${REGION:-asia-southeast1}"
SERVICE="${SERVICE:-sbi-smart-agent}"
MODEL="${SBI_MODEL:-claude-sonnet-4-6}"
USE_FIRESTORE="${USE_FIRESTORE:-1}"
SECRET_NAME="anthropic-api-key"

echo "▶ Project : $PROJECT_ID"
echo "▶ Region  : $REGION"
echo "▶ Service : $SERVICE"
echo "▶ Model   : $MODEL"
echo

# 1) Chọn project
gcloud config set project "$PROJECT_ID"

# 2) Bật các API cần thiết
echo "▶ Bật các API cần thiết…"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com

# 3) Đảm bảo secret tồn tại (để trang /admin nạp key sau) + thêm version nếu có key
echo "▶ Thiết lập secret '$SECRET_NAME'…"
if ! gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
  gcloud secrets create "$SECRET_NAME" --replication-policy=automatic
fi
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  printf '%s' "$ANTHROPIC_API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
fi

# 4) Cấp quyền cho service account runtime: ĐỌC key + THÊM version (nạp key từ /admin)
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "▶ Cấp quyền secret cho $RUNTIME_SA…"
for ROLE in roles/secretmanager.secretAccessor roles/secretmanager.secretVersionAdder; do
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:${RUNTIME_SA}" --role="$ROLE" >/dev/null 2>&1 || true
done

# Chỉ inject secret thành biến môi trường nếu đã có version (tránh deploy lỗi)
if gcloud secrets versions access latest --secret="$SECRET_NAME" >/dev/null 2>&1; then
  SECRET_FLAG=(--set-secrets "ANTHROPIC_API_KEY=${SECRET_NAME}:latest")
else
  SECRET_FLAG=()
  echo "  (Secret chưa có version — app chạy demo cho tới khi bạn nạp key trong /admin.)"
fi

# 4b) Firestore (lưu lead & Q&A bền vững giữa các lần deploy / nhiều instance)
ENV_VARS="SBI_MODEL=${MODEL}"
if [[ "$USE_FIRESTORE" == "1" ]]; then
  echo "▶ Thiết lập Firestore…"
  gcloud firestore databases create --location="$REGION" --type=firestore-native 2>/dev/null \
    || echo "  (Firestore database đã tồn tại — bỏ qua)"
  PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/datastore.user" >/dev/null 2>&1 || true
  ENV_VARS="${ENV_VARS}##SBI_USE_FIRESTORE=auto##SBI_FIRESTORE_PROJECT=${PROJECT_ID}"
fi

# Secret Manager cho phép nạp/đọc API key lúc chạy (từ trang /admin)
ENV_VARS="${ENV_VARS}##SBI_USE_SECRET_MANAGER=auto##SBI_GCP_PROJECT=${PROJECT_ID}##SBI_API_KEY_SECRET=${SECRET_NAME}"

# Token quản trị (bật trang /admin) nếu được cung cấp
if [[ -n "${SBI_ADMIN_TOKEN:-}" ]]; then
  ENV_VARS="${ENV_VARS}##SBI_ADMIN_TOKEN=${SBI_ADMIN_TOKEN}"
  echo "▶ Trang /admin sẽ được bật."
else
  echo "⚠ Chưa set SBI_ADMIN_TOKEN — trang /admin sẽ bị tắt."
fi

# 5) Build & deploy (Cloud Build sẽ build từ Dockerfile)
echo "▶ Build & deploy lên Cloud Run…"
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 120 \
  --set-env-vars "^##^${ENV_VARS}" \
  "${SECRET_FLAG[@]}"

echo
echo "✅ Hoàn tất! URL dịch vụ:"
gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
