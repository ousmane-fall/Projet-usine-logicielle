output "vm_public_ip" {
  description = "IP publique de la VM Azure"
  value       = azurerm_public_ip.taskflow.ip_address
}

output "ssh_connection" {
  description = "Commande pour se connecter en SSH"
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.taskflow.ip_address}"
}

output "app_url" {
  description = "URL de l'application"
  value       = "http://${azurerm_public_ip.taskflow.ip_address}:5000/api/health"
}

output "grafana_url" {
  description = "URL Grafana"
  value       = "http://${azurerm_public_ip.taskflow.ip_address}:3000"
}

output "prometheus_url" {
  description = "URL Prometheus"
  value       = "http://${azurerm_public_ip.taskflow.ip_address}:9090"
}
