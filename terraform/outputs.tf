output "public_ip" {
  description = "IP publica de la VPS."
  value       = digitalocean_droplet.app.ipv4_address
}

output "ssh_command" {
  description = "Comando SSH sugerido."
  value       = "ssh root@${digitalocean_droplet.app.ipv4_address}"
}

output "app_url" {
  description = "URL de la aplicacion en el puerto usado por Docker Compose."
  value       = "http://${digitalocean_droplet.app.ipv4_address}:8080"
}

