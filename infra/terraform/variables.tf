variable "resource_group_name" {
  description = "Nom du Resource Group Azure"
  type        = string
  default     = "taskflow-rg"
}

variable "location" {
  description = "Région Azure"
  type        = string
  default     = "West Europe"
}

variable "vm_size" {
  description = "Taille de la VM Azure (Standard_B1s = la plus petite, gratuite avec crédits école)"
  type        = string
  default     = "Standard_B1s"
}

variable "admin_username" {
  description = "Utilisateur admin SSH de la VM"
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key" {
  description = "Clé SSH publique pour accéder à la VM (contenu de ~/.ssh/id_rsa.pub)"
  type        = string
}
