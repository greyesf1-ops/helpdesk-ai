# Guion de presentacion

Proyecto: HelpDesk AI, chatbot web de soporte tecnico con historial.

Integrantes:

- Javier
- Agusto
- Colchin
- Georgean

## Idea central

HelpDesk AI es una aplicacion web de IA para apoyar una mesa de ayuda de TI. El usuario escribe un problema tecnico, el sistema clasifica el caso, responde con pasos de diagnostico y guarda el historial en una base de datos PostgreSQL. La parte importante del proyecto no es solo el chatbot, sino que la solucion esta desplegada como un sistema administrable: VPS en AWS, Docker Compose, Terraform, CI/CD, persistencia y backup.

## Orden recomendado

Duracion sugerida: 8 a 12 minutos.

1. Problema y objetivo
2. Demo funcional
3. Arquitectura de aplicacion
4. Arquitectura de infraestructura
5. Docker y persistencia
6. CI/CD
7. Terraform
8. Backup y continuidad
9. Aprendizajes y mejoras

## Participacion por integrante

### Javier: problema, objetivo y demo inicial

Explicar:

- El problema es que muchas consultas de soporte se repiten y se pierden si no hay historial.
- El objetivo es crear un chatbot que ayude a diagnosticar incidentes y conserve evidencia.
- La aplicacion se usa desde una web desplegada en una VPS.

Frase sugerida:

```text
Nuestro proyecto se llama HelpDesk AI. Es un chatbot de soporte tecnico pensado para una mesa de ayuda. El usuario describe un problema, por ejemplo acceso a correo, red o contrasenas, y el sistema responde con pasos de diagnostico. Ademas, cada conversacion queda guardada para seguimiento.
```

Demo:

- Abrir http://18.212.132.228:8080
- Crear una nueva consulta.
- Escribir: "No puedo acceder al correo de la empresa".
- Mostrar que responde y clasifica como correo.

### Agusto: arquitectura e infraestructura AWS

Explicar:

- La aplicacion esta desplegada en AWS EC2.
- Terraform crea la instancia EC2, security group y key pair.
- La VPS usa Ubuntu.
- Los puertos abiertos son 22 para SSH, 80 y 8080 para web/demo.

Frase sugerida:

```text
Para cumplir Infrastructure as Code usamos Terraform. Con Terraform definimos la instancia EC2, la llave SSH, el security group y los outputs importantes como la IP publica, el comando SSH y la URL de la aplicacion. Esto evita que toda la infraestructura sea creada manualmente.
```

Mostrar:

- Carpeta `terraform/`.
- Archivo `main.tf`.
- Output de Terraform con `public_ip`, `ssh_command` y `app_url`.

### Colchin: Docker, persistencia y backup

Explicar:

- La solucion corre con Docker Compose.
- Hay tres servicios: frontend, backend y db.
- PostgreSQL guarda conversaciones y mensajes.
- El volumen `postgres_data` conserva la informacion.
- El script de backup genera un `.sql.gz`.

Frase sugerida:

```text
Usamos Docker Compose porque la solucion tiene varios servicios. El frontend corre con Nginx, el backend con FastAPI y la base de datos con PostgreSQL. La persistencia esta en PostgreSQL y se conserva con un volumen Docker. Para continuidad operativa agregamos un script de backup que exporta la base de datos en un archivo comprimido.
```

Mostrar comandos:

```bash
sudo docker compose ps
sudo sh scripts/backup.sh
ls -lh backups
```

### Georgean: backend, CI/CD y cierre

Explicar:

- El backend recibe mensajes desde el frontend.
- Detecta categoria del incidente.
- Usa OpenAI si existe API key; si no, responde con modo local para asegurar demo.
- GitHub Actions valida el proyecto.
- El workflow de deploy puede actualizar la VPS por SSH cuando se configuran secretos.

Frase sugerida:

```text
El backend esta hecho en FastAPI. Cuando recibe una consulta, guarda el mensaje, clasifica el incidente y genera una respuesta. Tambien dejamos un modo de respaldo sin API key para que la demo no dependa de un servicio externo. En CI/CD usamos GitHub Actions para validar el backend, revisar Docker Compose y dejar preparado el despliegue por SSH hacia la VPS.
```

Mostrar:

- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- Resultado de Actions en GitHub.

## Explicacion tecnica completa

### Flujo de uso

1. El usuario entra a la web.
2. El frontend carga el historial desde el backend.
3. El usuario envia una pregunta.
4. El backend guarda el mensaje en PostgreSQL.
5. El backend detecta la categoria del incidente.
6. El backend genera una respuesta.
7. La respuesta se guarda en PostgreSQL.
8. El frontend muestra la conversacion actualizada.

### Arquitectura

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

### Componentes desplegados

- `frontend`: interfaz web.
- `backend`: API y logica del chatbot.
- `db`: base de datos PostgreSQL.
- `postgres_data`: volumen persistente.

### Evidencia actual

- URL publica: http://18.212.132.228:8080
- Health check: http://18.212.132.228:8080/api/health
- Backup generado: `backups/helpdesk_ai_20260605_044216.sql.gz`
- Documento de evidencia: `docs/evidencia-despliegue.md`

## Preguntas que puede hacer el profesor

### Donde esta la persistencia?

En PostgreSQL. Las conversaciones se guardan en `conversations` y los mensajes en `messages`. Docker Compose usa el volumen `postgres_data`.

### Que pasa si se reinicia el contenedor?

La base de datos conserva la informacion porque el volumen de PostgreSQL sigue existiendo aunque se recree el contenedor.

### Que hizo Terraform?

Creo la infraestructura principal en AWS: instancia EC2, key pair, security group y outputs utiles.

### Que hizo Docker Compose?

Orquesto los tres servicios de la aplicacion: frontend, backend y base de datos.

### Que hace CI/CD?

El workflow `CI` valida dependencias del backend, compila Python, revisa Docker Compose y verifica archivos frontend. El workflow `Deploy VPS` esta preparado para desplegar por SSH cuando se configuran secretos.

### Como se recupera el sistema?

Se puede restaurar desde un backup SQL comprimido generado por `scripts/backup.sh` usando `scripts/restore.sh`.

### Por que AWS EC2 cuenta como VPS?

Porque EC2 provee una maquina virtual Linux accesible por SSH, con IP publica, firewall/security group y capacidad de ejecutar Docker.

## Cierre sugerido

```text
Como conclusion, HelpDesk AI demuestra una aplicacion web de IA funcional y administrable desde TI. No solo construimos el chatbot, sino tambien su despliegue real en AWS, contenedorizacion, persistencia, CI/CD, infraestructura como codigo y una estrategia basica de backup.
```

