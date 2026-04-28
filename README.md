# TaskFlow — Gestionnaire de tâches

Application Flask REST pour la gestion de tâches, avec pipeline CI/CD, stack de monitoring complète et infrastructure Azure as Code.

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | Python 3.12 · Flask · SQLAlchemy · SQLite |
| Conteneurisation | Docker · Docker Compose |
| Monitoring | Prometheus · Grafana · Loki · Promtail |
| Infrastructure | Terraform (Azure VM) · Ansible |
| CI/CD | GitHub Actions |
| Qualité | ruff · pytest · SonarCloud |

## Démarrage rapide

```bash
# Cloner et lancer la stack complète
docker compose up -d

# Application  → http://localhost:5000
# Prometheus   → http://localhost:9090
# Grafana      → http://localhost:3000  (admin / admin)
# Loki         → http://localhost:3100
```

## API REST

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | Santé de l'application |
| GET | `/api/tasks` | Lister les tâches (`?status=todo\|in_progress\|done`) |
| GET | `/api/tasks/:id` | Détail d'une tâche |
| POST | `/api/tasks` | Créer une tâche |
| PUT | `/api/tasks/:id` | Mettre à jour une tâche |
| DELETE | `/api/tasks/:id` | Supprimer une tâche |

**Exemple :**
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Ma tâche", "status": "todo"}'
```

## Développement local

```bash
pip install -r requirements.txt
python run.py
```

```bash
# Lancer les tests
pytest

# Linter
ruff check app/ tests/
```

## Infrastructure

Le dossier `infra/` contient :
- **Terraform** (`infra/terraform/`) : provisionne une VM Linux sur Azure
- **Ansible** (`infra/ansible/`) : déploie l'application sur la VM

Les secrets nécessaires (clés SSH, Service Principal Azure, token SonarCloud) sont configurés via `scripts/setup-secrets.sh`.

## CI/CD

- **CI** : lint ruff + tests pytest sur chaque push
- **CD** : build de l'image Docker, push sur GHCR, déploiement Ansible sur la VM Azure
