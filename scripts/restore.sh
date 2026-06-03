#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Uso: ./scripts/restore.sh backups/helpdesk_ai_YYYYmmdd_HHMMSS.sql.gz"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "No existe el archivo: ${BACKUP_FILE}"
  exit 1
fi

gunzip -c "${BACKUP_FILE}" | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'

echo "Restauracion completada desde: ${BACKUP_FILE}"

