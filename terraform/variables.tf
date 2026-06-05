variable "aws_region" {
  description = "Region de AWS donde se creara la instancia EC2."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto usado para etiquetar recursos."
  type        = string
  default     = "helpdesk-ai"
}

variable "instance_type" {
  description = "Tipo de instancia EC2. t3.micro suele ser suficiente para la demo."
  type        = string
  default     = "t3.micro"
}

variable "volume_size" {
  description = "Tamano del disco raiz en GB."
  type        = number
  default     = 20
}

variable "ssh_public_key" {
  description = "Llave publica SSH que Terraform registrara como key pair en AWS."
  type        = string
}

variable "ssh_allowed_ips" {
  description = "IPs autorizadas para SSH. Para una demo puede usarse 0.0.0.0/0, aunque no es ideal en produccion."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
