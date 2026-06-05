output "public_ip" {
  description = "IP publica de la instancia EC2."
  value       = aws_instance.app.public_ip
}

output "ssh_command" {
  description = "Comando SSH sugerido."
  value       = "ssh -i ~/.ssh/id_ed25519 ubuntu@${aws_instance.app.public_ip}"
}

output "app_url" {
  description = "URL de la aplicacion en el puerto usado por Docker Compose."
  value       = "http://${aws_instance.app.public_ip}:8080"
}
