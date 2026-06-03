variable "do_token" {
  description = "Token de API de DigitalOcean."
  type        = string
  sensitive   = true
}

variable "ssh_key_fingerprint" {
  description = "Fingerprint o ID de la llave SSH registrada en DigitalOcean."
  type        = string
}

variable "droplet_name" {
  description = "Nombre de la VPS."
  type        = string
  default     = "helpdesk-ai-vps"
}

variable "region" {
  description = "Region de DigitalOcean."
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "Tamano de la VPS."
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "ssh_allowed_ips" {
  description = "IPs autorizadas para SSH. Para clase puede usarse 0.0.0.0/0, aunque no es lo ideal en produccion."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

