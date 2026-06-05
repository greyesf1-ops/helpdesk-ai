# HelpDesk AI

Chatbot web de soporte tecnico con historial de conversaciones. El proyecto esta preparado para demostrar despliegue en VPS, Docker Compose, persistencia con PostgreSQL, CI/CD con GitHub Actions, Terraform y una estrategia basica de backup.

## Funcionalidades

- Chatbot para consultas de soporte tecnico.
- Historial persistente de conversaciones.
- Clasificacion basica de incidentes por categoria.
- Respuesta con OpenAI cuando existe `OPENAI_API_KEY`.
- Modo de respaldo local para demo sin API key.
- Interfaz web responsive.
- API REST con FastAPI.

## Arquitectura

```text
Usuario
  |
  v
Frontend Nginx :8080
  |
  v
Backend FastAPI :8000
  |
  v
PostgreSQL :5432
```

## Tecnologias

- Frontend: HTML, CSS y JavaScript
- Backend: Python, FastAPI, SQLAlchemy
- Base de datos: PostgreSQL
- Contenedores: Docker y Docker Compose
- CI/CD: GitHub Actions
- IaC: Terraform
- VPS objetivo: Linux Ubuntu

## Ejecucion local con Docker

1. Copia las variables de entorno:

```bash
cp .env.example .env
```

2. Edita `.env` y define tus valores. Para una demo sin OpenAI, puedes dejar `OPENAI_API_KEY` vacia.

3. Levanta la solucion:

```bash
docker compose up -d --build
```

4. Abre la aplicacion:

```text
http://localhost:8080
```

5. Revisa el estado:

```bash
docker compose ps
curl http://localhost:8080/api/health
```

## Variables de entorno

| Variable | Descripcion |
| --- | --- |
| `POSTGRES_DB` | Nombre de la base de datos |
| `POSTGRES_USER` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | Password de PostgreSQL |
| `DATABASE_URL` | URL de conexion usada por el backend |
| `OPENAI_API_KEY` | API key de OpenAI, opcional para demo |
| `OPENAI_MODEL` | Modelo usado por el backend |
| `APP_ENV` | Ambiente de ejecucion |

## Persistencia

El estado principal vive en PostgreSQL:

- Conversaciones en la tabla `conversations`.
- Mensajes de usuario y asistente en la tabla `messages`.
- Categoria detectada para cada mensaje.

Docker Compose usa el volumen `postgres_data`, por lo que la base de datos no se pierde al recrear contenedores.

## Backup y recuperacion

El script `scripts/backup.sh` genera un respaldo SQL comprimido de PostgreSQL en la carpeta `backups/`.

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

Para restaurar:

```bash
chmod +x scripts/restore.sh
./scripts/restore.sh backups/helpdesk_ai_YYYYmmdd_HHMMSS.sql.gz
```

En VPS se recomienda programar el backup con cron:

```cron
0 2 * * * cd /opt/helpdesk-ai && ./scripts/backup.sh
```

## CI/CD

El repositorio incluye:

- `.github/workflows/ci.yml`: valida backend, frontend y configuracion de Docker Compose.
- `.github/workflows/deploy.yml`: despliega por SSH en la VPS cuando se actualiza `main`.

Secretos requeridos para despliegue:

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `APP_DIR`

## Terraform

La carpeta `terraform/` contiene una configuracion base para crear una VPS en DigitalOcean.

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Variables principales:

- `do_token`
- `ssh_key_fingerprint`
- `region`
- `droplet_size`
- `droplet_name`

Outputs utiles:

- IP publica de la VPS.
- Comando SSH.
- URL base de la aplicacion.

## Despliegue manual en VPS

1. Crear la VPS con Terraform.
2. Entrar por SSH.
3. Instalar Docker si no se uso el `user_data` incluido:

```bash
sudo ./scripts/server-bootstrap-ubuntu.sh
```

4. Clonar el repositorio en `/opt/helpdesk-ai`, crear `.env` y levantar contenedores:

```bash
sudo APP_DIR=/opt/helpdesk-ai REPO_URL=https://github.com/greyesf1-ops/helpdesk-ai.git ./scripts/deploy-vps.sh
```

Tambien se puede hacer manualmente:

```bash
cd /opt
git clone https://github.com/greyesf1-ops/helpdesk-ai.git
cd helpdesk-ai
cp .env.example .env
docker compose up -d --build
```

## Operacion basica

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose restart backend
```
