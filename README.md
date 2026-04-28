# TaskFlow — Usine Logicielle DevOps

API REST de gestion de tâches construite autour d'un pipeline DevOps complet :
CI/CD GitHub Actions, conteneurisation Docker, monitoring Prometheus/Grafana,
logs structurés Loki/Promtail, IaC Terraform/Ansible sur Azure.

---

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | Python 3.12 · Flask 3 · SQLAlchemy · SQLite |
| Conteneurisation | Docker multi-stage · Docker Compose |
| CI/CD | GitHub Actions (lint, test, sécurité, build, deploy) |
| Qualité | ruff · pylint · mypy · bandit · pip-audit · radon · SonarCloud |
| Tests | pytest · pytest-cov (seuil 80%) |
| Monitoring | Prometheus · Grafana |
| Logs | Loki · Promtail (pipeline JSON) |
| IaC | Terraform (Azure VM) · Ansible |

---

## Démarrage rapide

```bash
# 1. Copier et adapter les variables d'environnement
cp .env.example .env
# Editer .env : SECRET_KEY, GRAFANA_ADMIN_PASSWORD

# 2. Lancer la stack complète
docker compose up -d

# Services
# Application  -> http://localhost:5000
# Prometheus   -> http://localhost:9090
# Grafana      -> http://localhost:3000  (admin / voir .env)
# Loki         -> http://localhost:3100
```

---

## API REST

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | Statut de l'application |
| GET | `/metrics` | Métriques Prometheus |
| GET | `/api/tasks` | Lister les tâches (`?status=todo\|in_progress\|done`) |
| GET | `/api/tasks/:id` | Détail d'une tâche |
| POST | `/api/tasks` | Créer une tâche |
| PUT | `/api/tasks/:id` | Mettre à jour une tâche |
| DELETE | `/api/tasks/:id` | Supprimer une tâche |
| POST | `/api/calculate` | Calculatrice (expression ou opération) |
| POST | `/api/validate` | Validation email/username |

**Exemple :**
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Ma tache", "status": "todo"}'

curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression": "1 + 2 * 3"}'
# {"result": 7}
```

---

## Développement local

```bash
# Installer les dépendances prod + dev
pip install -r requirements.txt -r requirements-dev.txt

# Lancer en mode développement
python run.py

# Lancer les tests
pytest --cov=app --cov-report=term-missing

# Lancer tous les checks qualité
./scripts/quality_check.sh --fast
```

---

## CI/CD

### Pipeline CI (`.github/workflows/ci.yml`)

```
push/PR -> quality -> test -> sonar -> docker-build
          (ruff, pylint,   (pytest      (SonarCloud)  (GHCR)
           mypy, bandit,    coverage
           pip-audit)       >= 80%)
```

Chaque job dépend du précédent. Une erreur bloque la suite.

### Pipeline CD (`.github/workflows/cd.yml`)

Se déclenche quand CI passe sur `main` :

```
smoke-test -> terraform -> deploy
(docker run  (fmt+validate  (ansible-playbook
 curl health  + apply)       + smoke test VM)
```

- Job `terraform` et `deploy` sont dans l'**environment GitHub `production`** (approbation manuelle requise).
- Smoke test local puis smoke test distant sur `/api/health`.

### Secrets requis

| Secret | Description |
|---|---|
| `AZURE_CLIENT_ID` | Service Principal Azure |
| `AZURE_CLIENT_SECRET` | Secret du SP |
| `AZURE_SUBSCRIPTION_ID` | ID abonnement Azure |
| `AZURE_TENANT_ID` | ID tenant Azure |
| `VM_SSH_PUBLIC_KEY` | Clé publique SSH |
| `VM_SSH_PRIVATE_KEY` | Clé privée SSH |
| `SONAR_TOKEN` | Token SonarCloud |

Configurer automatiquement via :
```bash
./scripts/setup-secrets.sh
```

---

## Docker

### Image

```bash
# Build
docker build -t taskflow .

# Run
docker run -p 5000:5000 -e SECRET_KEY=monsecret taskflow
```

L'image est **multi-stage**, tourne en **utilisateur non-root** et expose un
`HEALTHCHECK` sur `/api/health`. Le serveur de production est **gunicorn** (4 workers).

### Compose

Variables clés dans `.env` :

| Variable | Défaut | Description |
|---|---|---|
| `SECRET_KEY` | — | **Obligatoire** en production |
| `FLASK_ENV` | `production` | Mode Flask |
| `GRAFANA_ADMIN_PASSWORD` | — | Mot de passe Grafana |
| `APP_PORT` | `5000` | Port exposé app |

---

## Monitoring

### Prometheus

- Scrape de `/metrics` (via `prometheus_flask_exporter`) toutes les 10s
- Labels `service` et `environment` sur toutes les métriques
- Config : `monitoring/prometheus/prometheus.yml`

### Grafana

- Datasources provisionnées automatiquement (Prometheus + Loki)
- Dashboard TaskFlow : `monitoring/grafana/dashboards/taskflow.json`
- Accès : http://localhost:3000

---

## Logs

Flask émet des logs en **JSON structuré** :

```json
{"time": "...", "level": "INFO", "logger": "app.api", "message": "Listed 3 tasks"}
```

Promtail collecte les conteneurs Docker labelisés `logging: promtail`, parse
le JSON et promouvoit `level`/`logger` en labels Loki.

Requêtes Loki utiles dans Grafana :
```
{service="taskflow"} | json | level="ERROR"
{container_name="taskflow-app"} | json | message != ""
```

---

## Infrastructure as Code

### Terraform (`infra/terraform/`)

Provisionne sur Azure :
- Resource Group, VNet, Subnet, IP publique
- NSG : SSH (22), App (5000) ouverts ; Grafana/Prometheus restreints à `allowed_monitoring_cidr`
- VM Ubuntu 22.04 LTS (Standard_B1s)
- State distant sur Azure Blob Storage (`backend.tf`)

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
# Editer terraform.tfvars
cd infra/terraform
terraform init && terraform apply
```

### Ansible (`infra/ansible/`)

Roles :
- `docker` : installation Docker + Docker Compose
- `app` : déploiement de la stack (docker-compose.yml + monitoring/)
- `monitoring` : configuration Promtail sur la VM

```bash
ansible-playbook -i infra/ansible/inventory.ini infra/ansible/playbook.yml \
  --extra-vars "image_tag=latest app_image=ghcr.io/ousmane-fall/taskflow"
```

---

## Qualité de code

| Outil | Rôle | Seuil |
|---|---|---|
| ruff | Lint + format | 0 erreur |
| pylint | Analyse statique | score >= 7/10 |
| mypy | Vérification de types | 0 erreur |
| bandit | Sécurité du code | 0 HIGH/MEDIUM |
| pip-audit | CVE dans les deps | 0 vulnérabilité |
| radon | Complexité cyclomatique | grade B min |
| pytest-cov | Couverture de tests | >= 80% |
| SonarCloud | Analyse globale | Quality Gate pass |

Lancer localement :
```bash
./scripts/quality_check.sh
```

---

## Sécurité

- `SECRET_KEY` lue depuis l'environnement — obligatoire en production
- Dockerfile : utilisateur non-root, image slim, HEALTHCHECK
- Pas de secrets en clair dans le code ou les workflows
- NSG Azure restreint pour les ports monitoring
- Expressions arithmétiques évaluées via `ast` (jamais `eval`)
- Validation des entrées email/username avec regex stricte

---

## Limites connues

- Base de données SQLite — à remplacer par PostgreSQL en production
- Pas de pagination sur `GET /api/tasks`
- State Terraform local par défaut (configurer `backend.tf` pour le CI)
- Un seul worker Gunicorn pour les tests — augmenter `-w` selon la charge

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
