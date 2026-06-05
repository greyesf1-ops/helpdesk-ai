# Evidencia de despliegue

Fecha de verificacion: 2026-06-05

## Infraestructura

- Proveedor: AWS
- Servicio: EC2
- Region: us-east-1
- IP publica: 18.212.132.228
- URL de la aplicacion: http://18.212.132.228:8080
- Usuario SSH: ubuntu

## Terraform

Terraform creo 3 recursos principales:

- `aws_key_pair.app`
- `aws_security_group.app`
- `aws_instance.app`

Outputs generados:

```text
app_url = "http://18.212.132.228:8080"
public_ip = "18.212.132.228"
ssh_command = "ssh -i ~/.ssh/id_ed25519 ubuntu@18.212.132.228"
```

## Estado de servicios

Contenedores desplegados en la VPS:

```text
helpdesk_ai_db         postgres:16-alpine     Up, healthy
helpdesk_ai_backend    helpdesk-ai-backend    Up
helpdesk_ai_frontend   helpdesk-ai-frontend   Up, 0.0.0.0:8080->80/tcp
```

## Pruebas realizadas

Endpoint de salud:

```text
GET http://18.212.132.228:8080/api/health
Respuesta: {"status":"ok","service":"helpdesk-ai-backend"}
```

Prueba funcional:

- Se creo una conversacion de prueba.
- Se envio el mensaje: "No puedo acceder al correo de la empresa".
- El sistema clasifico el caso como `correo`.
- El asistente respondio con pasos de diagnostico.
- Los mensajes quedaron guardados en PostgreSQL.

## Backup

Se ejecuto:

```bash
sudo sh scripts/backup.sh
```

Archivo generado:

```text
backups/helpdesk_ai_20260605_044216.sql.gz
```

