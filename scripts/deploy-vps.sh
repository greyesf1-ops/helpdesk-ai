#!/usr/bin/env sh
set -eu

APP_DIR="${APP_DIR:-/opt/helpdesk-ai}"
REPO_URL="${REPO_URL:-https://github.com/greyesf1-ops/helpdesk-ai.git}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecuta este script como root o con sudo."
  exit 1
fi

if [ ! -d "${APP_DIR}/.git" ]; then
  rm -rf "${APP_DIR}"
  git clone "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
git pull origin main

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Se creo .env desde .env.example. Revisa las variables antes de produccion."
fi

docker compose up -d --build
docker compose ps

echo "Despliegue completado. Abre http://IP_DE_LA_VPS:8080"

