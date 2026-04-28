# Infrastructure as Code — TaskFlow

## Terraform (Azure)

Provisionne l'infrastructure minimale sur Azure :
- 1 Resource Group
- 1 VNet + 1 Subnet
- 1 IP publique
- 1 NSG (SSH 22, App 5000, Grafana 3000, Prometheus 9090)
- 1 VM Ubuntu 22.04 (Standard_B1s)

### Utilisation

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Éditer terraform.tfvars (au minimum : ssh_public_key)

terraform init
terraform plan
terraform apply
```

### State

Par défaut le **state Terraform est local** (`terraform.tfstate`).
Il est exclu du Git via `.gitignore`.

> En production, utiliser un **backend distant** (Azure Blob Storage, S3, etc.)
> pour permettre le travail en équipe et le CI/CD multi-runs.
> Voir https://developer.hashicorp.com/terraform/language/settings/backends/azurerm

### Sécurité

Pour restreindre l'accès aux ports monitoring (Grafana 3000, Prometheus 9090)
à votre seule IP, modifier dans `terraform.tfvars` :

```hcl
allowed_monitoring_cidr = "203.0.113.42/32"
```

## Ansible

Déploie la stack Docker Compose sur la VM provisionnée par Terraform.

### Roles

- `docker` : installe Docker et Docker Compose v2
- `app` : copie `docker-compose.yml` + `monitoring/` et démarre la stack
- `monitoring` : configuration Promtail sur la VM

### Utilisation

```bash
# Récupérer l'IP de la VM
cd infra/terraform
VM_IP=$(terraform output -raw vm_public_ip)

# Mettre à jour l'inventaire
cd ../ansible
sed -i "s/VM_IP_PLACEHOLDER/$VM_IP/" inventory.ini

# Lancer le playbook
ansible-playbook -i inventory.ini playbook.yml \
  --extra-vars "image_tag=latest app_image=ghcr.io/<your-user>/taskflow"
```

## Limites et améliorations possibles

- Backend Terraform distant (Azure Blob Storage) pour le travail en équipe
- Module Terraform réutilisable au lieu d'un fichier monolithique
- Restriction IP plus fine sur le NSG (par défaut ouvert au monde)
- Certificat HTTPS (Let's Encrypt) au lieu de HTTP
- Sauvegarde automatique du volume SQLite
