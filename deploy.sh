#!/usr/bin/env bash
#
# Deploy SBI Smart Agent lên Google Cloud Run.
#
# Cách dùng (chạy trên Google Cloud Shell hoặc máy đã cài gcloud):
#   export ANTHROPIC_API_KEY="sk-ant-..."   # API key Claude của bạn
#   ./deploy.sh
#
# Có thể tuỳ chỉnh qua biến môi trường:
#   PROJECT_ID (mặc định: sbi-smart-agent)
#   REGION     (mặc định: asia-southeast1 - Singapore)
#   SERVICE    (mặc định: sbi-smart-agent)
#   SBI_MODEL  (mặc định: claude-sonnet-4-6)
#
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-sbi-smart-agent}"
REGION="${REGION:-asia-southeast1}"
SERVICE="${SERVICE:-sbi-smart-agent}"
MODEL="${SBI_MODEL:-claude-sonnet-4-6}"
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
  artifactregistry.googleapis.com

# 3) Lưu API key vào Secret Manager (nếu cung cấp qua biến môi trường)
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "▶ Cập nhật secret '$SECRET_NAME'…"
  if gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
    printf '%s' "$ANTHROPIC_API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
  else
    printf '%s' "$ANTHROPIC_API_KEY" | gcloud secrets create "$SECRET_NAME" \
      --data-file=- --replication-policy=automatic
  fi
else
  echo "⚠ Chưa set ANTHROPIC_API_KEY. Bỏ qua bước tạo secret."
  echo "  (App sẽ chạy ở 'demo mode' nếu secret chưa tồn tại.)"
fi

# 4) Cấp quyền cho service account runtime đọc secret
if gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
  PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
  echo "▶ Cấp quyền đọc secret cho $RUNTIME_SA…"
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
  SECRET_FLAG=(--set-secrets "ANTHROPIC_API_KEY=${SECRET_NAME}:latest")
else
  SECRET_FLAG=()
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
  --set-env-vars "SBI_MODEL=${MODEL}" \
  "${SECRET_FLAG[@]}"

echo
echo "✅ Hoàn tất! URL dịch vụ:"
gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
