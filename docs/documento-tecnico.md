# Documento tecnico del proyecto

## Nombre del proyecto

HelpDesk AI: Chatbot de soporte tecnico con historial.

## Integrantes

- Javier
- Agusto
- Colchin
- Georgean

## Descripcion del problema

Muchas organizaciones reciben solicitudes repetitivas de soporte tecnico relacionadas con acceso, red, correo, impresoras, rendimiento y recuperacion de archivos. Cuando estas consultas no se registran de forma ordenada, se pierde historial, evidencia y trazabilidad operativa.

## Objetivo del sistema

Desarrollar una aplicacion web de IA que atienda consultas basicas de soporte tecnico, sugiera pasos de diagnostico y conserve el historial de conversaciones para administracion y seguimiento.

## Funcionalidades principales

- Crear conversaciones de soporte.
- Enviar preguntas tecnicas al chatbot.
- Adjuntar imagenes o capturas como evidencia del caso.
- Recibir respuestas con recomendaciones operativas.
- Clasificar incidentes por categoria.
- Consultar historial de conversaciones.
- Mantener la informacion en una base de datos persistente.

## Arquitectura general de la aplicacion

La solucion se compone de tres servicios:

- Frontend web servido con Nginx.
- Backend API construido con FastAPI.
- Base de datos PostgreSQL.

El usuario accede al frontend. El frontend consume endpoints `/api`. Nginx redirige esas solicitudes al backend. El backend procesa el mensaje, guarda imagenes adjuntas cuando existen, consulta el historial, genera una respuesta con IA o modo de respaldo y guarda mensajes en PostgreSQL.

## Arquitectura de infraestructura

La infraestructura objetivo es una VPS Linux Ubuntu creada con Terraform sobre AWS EC2. En la VPS se ejecuta Docker y Docker Compose. Los contenedores se comunican por una red interna de Compose y solo se publica el puerto web.

## Tecnologias utilizadas

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL 16
- OpenAI API opcional
- HTML, CSS y JavaScript
- Nginx
- Docker
- Docker Compose
- GitHub Actions
- Terraform
- AWS EC2 como proveedor de VPS

## Flujo general del sistema

1. El usuario abre la interfaz web.
2. La interfaz consulta el estado del backend.
3. El usuario crea o selecciona una conversacion.
4. El usuario envia una consulta tecnica.
5. Opcionalmente adjunta una imagen o captura del error.
6. El backend guarda el mensaje del usuario y la referencia del adjunto.
7. El backend detecta una categoria.
8. El backend genera una respuesta con OpenAI si existe API key; si no, usa modo de respaldo local.
9. El backend guarda la respuesta.
10. El frontend actualiza el historial.

## Despliegue en VPS

El despliegue se realiza en una VPS Ubuntu sobre AWS EC2. Terraform crea la instancia EC2, registra una llave SSH, abre puertos necesarios mediante un security group y ejecuta una configuracion inicial para instalar Docker. Luego el repositorio se clona en `/opt/helpdesk-ai`, se crea el archivo `.env` y se ejecuta `docker compose up -d --build`.

## Uso de Docker y Docker Compose

Docker se usa para empaquetar cada componente:

- `frontend`: Nginx con archivos estaticos y proxy para `/api` y `/uploads`.
- `backend`: aplicacion FastAPI.
- `db`: PostgreSQL.

Docker Compose define dependencias, variables, red interna, volumen de base de datos, volumen de adjuntos y puertos publicados.

## Pipeline CI/CD

El pipeline de CI ejecuta validaciones en cada push o pull request hacia `main`:

- Instalacion de dependencias del backend.
- Compilacion del codigo Python.
- Validacion de `docker-compose.yml`.
- Verificacion de archivos frontend.

El pipeline de despliegue usa SSH para conectarse a la VPS, actualizar el repositorio y recrear los contenedores con Docker Compose.

## Infrastructure as Code con Terraform

Terraform define:

- Instancia EC2 principal.
- Variables de region, tipo de instancia, tamano de disco, nombre y llave SSH.
- Security group basico.
- Outputs con IP publica, comando SSH y URL de la aplicacion.
- Configuracion inicial para instalar Docker.

Esto permite evidenciar que la infraestructura principal no fue creada unicamente de forma manual.

## Persistencia

La persistencia vive en PostgreSQL. Las tablas principales son:

- `conversations`: guarda conversaciones.
- `messages`: guarda mensajes de usuario y asistente, categoria y URL de imagen adjunta.

El volumen Docker `postgres_data` conserva la informacion incluso si se recrean los contenedores. El volumen `uploads_data` conserva las imagenes cargadas por los usuarios.

## Backup y continuidad

La estrategia basica de continuidad consiste en:

- Generar backups periodicos de PostgreSQL con `scripts/backup.sh`.
- Guardar los respaldos comprimidos en la carpeta `backups/`.
- Restaurar un respaldo con `scripts/restore.sh`.
- Documentar los componentes criticos: VPS, base de datos, archivo `.env`, imagenes Docker, volumen de adjuntos y repositorio GitHub.

En operacion real se recomienda copiar los backups a almacenamiento externo, por ejemplo un bucket o una carpeta segura fuera de la VPS.

## Decisiones tecnicas importantes

- Se usa PostgreSQL porque permite persistencia clara y facil de respaldar.
- Se agrega carga de imagenes para guardar evidencia visual de incidentes.
- Se usa Nginx para servir el frontend y redirigir llamadas API.
- Se incluye modo de respaldo sin API key para asegurar demo funcional.
- Se usa Docker Compose porque existen multiples servicios.
- Se usa Terraform para representar la VPS como codigo.

## Limitaciones actuales

- No tiene autenticacion de usuarios.
- No incluye panel administrativo avanzado.
- El modo local de IA es basico y no reemplaza un modelo real.
- El despliegue usa HTTP; en produccion deberia agregarse HTTPS.

## Mejoras futuras

- Agregar autenticacion y roles.
- Crear panel de tickets.
- Agregar metricas operativas.
- Agregar almacenamiento externo para adjuntos, por ejemplo S3.
- Agregar HTTPS con reverse proxy y certificados.
- Usar busqueda semantica sobre una base de conocimiento.
