# TaskFlow — Projet Usine Logicielle

API REST de gestion de tâches (Flask) servant de support à un projet
d'usine logicielle DevOps : tests, qualité, conteneurisation, CI/CD,
monitoring, logs et infrastructure as code.

Projet pédagogique — l'objectif est de couvrir toutes les briques d'une
usine logicielle dans une architecture **simple et compréhensible**.

---

## Sommaire

1. [Stack technique](#stack-technique)
2. [Démarrage rapide (Docker Compose)](#démarrage-rapide)
3. [API REST](#api-rest)
4. [Développement local](#développement-local)
5. [Tests et qualité](#tests-et-qualité)
6. [CI/CD](#cicd)
7. [Monitoring et logs](#monitoring-et-logs)
8. [Déploiement Azure manuel](#déploiement-azure-manuel)
9. [Sécurité](#sécurité)
10. [Limites et améliorations possibles](#limites-et-améliorations-possibles)

---

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | Python 3.12 · Flask 3 · SQLAlchemy · SQLite |
| Conteneurisation | Docker (multi-stage, non-root) · Docker Compose |
| CI/CD | GitHub Actions |
| Qualité | ruff · pylint · mypy · bandit · pytest-cov |
| Monitoring | Prometheus · Grafana |
| Logs | Loki · Promtail |
| IaC | Terraform · Ansible (Azure) |

---

## Démarrage rapide

Prérequis : Docker Desktop ou Docker Engine + Docker Compose v2.

```bash
# 1. Créer le fichier .env à partir du modèle
cp .env.example .env
# Editer .env : SECRET_KEY et GRAFANA_ADMIN_PASSWORD

# 2. Lancer la stack complète
docker compose up -d

# 3. Vérifier
curl http://localhost:5000/api/health
```

| Service | URL |
|---|---|
| Application | http://localhost:5000 |
| Métriques | http://localhost:5000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Loki | http://localhost:3100 |

Pour tout arrêter : `docker compose down`. Pour effacer les volumes : `docker compose down -v`.

---

## API REST

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | Statut |
| GET | `/api/tasks` | Lister (`?status=todo\|in_progress\|done`) |
| GET | `/api/tasks/:id` | Détail |
| POST | `/api/tasks` | Créer (`title` requis) |
| PUT | `/api/tasks/:id` | Mettre à jour |
| DELETE | `/api/tasks/:id` | Supprimer |
| POST | `/api/calculate` | Calculatrice (expression OU opération) |
| POST | `/api/validate` | Validation email / username |

Exemples :
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Ma tache","status":"todo"}'

curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"1 + 2 * 3"}'
# {"result": 7}
```

---

## Développement local

```bash
# Installer les dépendances (prod + dev)
pip install -r requirements.txt -r requirements-dev.txt

# Lancer l'app en mode développement (serveur Flask)
python run.py

# Lancer les tests
pytest --cov=app --cov-report=term-missing
```

Lancer **tous les checks qualité** d'un coup :
```bash
./scripts/quality_check.sh
./scripts/quality_check.sh --fast   # sans pip-audit ni radon
```

---

## Tests et qualité

| Outil | Rôle | Commande |
|---|---|---|
| ruff | Lint + format | `ruff check app/ tests/` |
| pylint | Analyse statique | `pylint app/` |
| mypy | Vérification de types | `mypy` |
| bandit | Sécurité du code | `bandit -r app/` |
| pytest + pytest-cov | Tests + couverture | `pytest --cov=app` |
| pip-audit | CVE des deps (informatif) | `pip-audit` |
| radon | Complexité | `radon cc app/ -a` |

**Couverture actuelle : ~96%** (seuil enforced en CI : 80%).

---

## CI/CD

### CI — `.github/workflows/ci.yml`

```
push / PR
   |
   ├── quality          ruff, pylint, mypy, bandit (+ pip-audit informatif)
   ├── test             pytest --cov-fail-under=80
   ├── sonar (optionnel) skip si SONAR_TOKEN absent
   └── docker-build     push image vers GHCR (sur main et dev)
```

Toute erreur dans `quality` ou `test` **fait échouer** le pipeline.
SonarCloud est facultatif : pas de token = job skip, pas d'échec.

### CD — `.github/workflows/cd.yml`

Le CD est **volontairement simplifié** : il ne déploie pas automatiquement
sur Azure. Il valide uniquement que tout est prêt à déployer.

```
CI passe sur main
   |
   ├── docker-smoke-test   build + curl /api/health
   └── terraform-validate  fmt + validate
```

Le déploiement réel sur Azure se fait **manuellement** (voir section ci-dessous).

### Secrets GitHub nécessaires

| Secret | Obligatoire ? | Usage |
|---|---|---|
| `GITHUB_TOKEN` | auto | Push image vers GHCR |
| `SONAR_TOKEN` | non | Active SonarCloud (optionnel) |

Pour le déploiement Azure manuel, aucun secret CI n'est requis.

---

## Monitoring et logs

### Prometheus

L'app expose `/metrics` via `prometheus_flask_exporter`.
Prometheus le scrape toutes les 10s avec les labels `service=taskflow`
et `environment=production`.

Configuration : [monitoring/prometheus/prometheus.yml](monitoring/prometheus/prometheus.yml)

### Grafana

Datasources Prometheus et Loki provisionnées automatiquement.
Dashboard TaskFlow disponible dès le premier démarrage.

Login par défaut : `admin` / valeur de `GRAFANA_ADMIN_PASSWORD` dans `.env`.

### Logs structurés (Loki + Promtail)

Flask émet des logs en JSON :
```json
{"time":"2026-04-29 10:00:00,000","level":"INFO","logger":"app.api","message":"Listed 3 tasks"}
```

Promtail parse le JSON et promouvoit `level` et `logger` en labels Loki.

Requêtes utiles dans Grafana :
```
{service="taskflow"} | json | level="ERROR"
{container_name="taskflow-app"}
```

---

## Déploiement Azure manuel

> Le CD ne déploie pas automatiquement sur Azure pour rester simple et
> éviter de provisionner involontairement des ressources payantes.
> Le déploiement se fait **à la main** en suivant ces étapes.

### Prérequis

```bash
# Installer Azure CLI, Terraform et Ansible
az login
```

### 1. Provisionner la VM (Terraform)

```bash
cd infra/terraform

# Créer le fichier de variables
cp terraform.tfvars.example terraform.tfvars
# Editer terraform.tfvars : ssh_public_key, allowed_monitoring_cidr

terraform init
terraform plan
terraform apply

# Récupérer l'IP de la VM
terraform output vm_public_ip
```

### 2. Déployer l'application (Ansible)

```bash
cd ../ansible

# Adapter inventory.ini avec l'IP retournée par Terraform
# (remplacer la ligne ansible_host=...)

ansible-playbook -i inventory.ini playbook.yml \
  --extra-vars "image_tag=latest app_image=ghcr.io/<your-user>/taskflow"
```

### 3. Vérifier

```bash
curl http://<vm_public_ip>:5000/api/health
```

### 4. Détruire (très important pour ne pas payer)

```bash
cd ../terraform
terraform destroy
```

Voir [infra/README.md](infra/README.md) pour plus de détails.

---

## Sécurité

- `SECRET_KEY` lue depuis l'environnement — obligatoire en production (`FLASK_ENV=production`)
- Image Docker : utilisateur **non-root** (`appuser`), multi-stage, HEALTHCHECK
- Mot de passe Grafana via variable d'environnement (jamais en dur)
- Évaluation arithmétique via `ast` (jamais `eval`) — résistant à l'injection
- Validation stricte des entrées (regex + AST whitelist)
- `bandit` exécuté en CI sur chaque commit

---

## Limites et améliorations possibles

Le projet privilégie la simplicité pédagogique. Voici les améliorations
qui auraient leur place dans un contexte de production :

- **Backend Terraform distant** (Azure Blob Storage / S3) au lieu du state local
- **Déploiement automatique CD** vers Azure (actuellement manuel par sécurité)
- **SonarCloud obligatoire** dans la CI (actuellement optionnel)
- **pip-audit bloquant** au lieu d'informatif (actuellement non-bloquant car les CVE deps évoluent constamment)
- **Restriction réseau plus fine** sur le NSG Azure (actuellement ouvert au monde)
- **Certificat HTTPS** (Let's Encrypt) au lieu d'HTTP en clair
- **Base PostgreSQL** au lieu de SQLite pour la production
- **Alertmanager** + règles d'alerte Prometheus
- **Trivy** (scan d'image Docker) et **hadolint** (lint Dockerfile) en CI
- **Sauvegarde automatique** du volume SQLite et des dashboards Grafana
- **Multi-environnements** (dev / staging / prod) avec workspaces Terraform

---

## Documentation complémentaire

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — schéma d'architecture
- [QUALITY_REPORT.md](QUALITY_REPORT.md) — rapport qualité détaillé
- [infra/README.md](infra/README.md) — Terraform + Ansible
