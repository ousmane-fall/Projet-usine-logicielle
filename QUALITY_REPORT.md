# Rapport Qualité — TaskFlow

Document récapitulatif de la démarche qualité du projet.
Approche **honnête** : on indique ce qui est automatisé, ce qui est manuel,
et ce qui pourrait être amélioré.

---

## 1. Tests

| Type | Outil | Localisation | Statut |
|---|---|---|---|
| Unitaires | pytest | `tests/unit/` | ✅ Automatisé en CI |
| Intégration API | pytest + Flask test client | `tests/integration/` | ✅ Automatisé en CI |
| Couverture | pytest-cov | — | ✅ Seuil bloquant 80% |

**Couverture actuelle : ~96%**
- `app/__init__.py` : 84%
- `app/api.py` : 97%
- `app/calculator.py` : 96%
- `app/models.py` : 100%
- `app/validators.py` : 100%

Commande locale : `pytest --cov=app --cov-report=term-missing`

---

## 2. Analyse statique

| Outil | Rôle | Bloquant en CI ? |
|---|---|---|
| **ruff** | Lint + format (E, F, I, N, W, B, UP, SIM, C4) | ✅ Oui |
| **pylint** | Analyse statique (seuil 7.0/10) | ✅ Oui |
| **mypy** | Vérification de types (strict sur `app/`) | ✅ Oui |
| **bandit** | Sécurité du code Python | ✅ Oui |
| **radon** | Complexité cyclomatique | ❌ Informatif |

Configuration : [pyproject.toml](pyproject.toml), [.pylintrc](.pylintrc), [mypy.ini](mypy.ini)

---

## 3. Sécurité

| Aspect | Mise en œuvre |
|---|---|
| Secrets | Variables d'environnement (jamais en dur) — `SECRET_KEY` requis en prod |
| Image Docker | Non-root, multi-stage, HEALTHCHECK |
| Scan code | bandit en CI |
| Scan deps | pip-audit (informatif, voir limites) |
| Évaluation arithmétique | `ast` whitelist (pas d'`eval`) |
| Validation entrées | Regex stricts + tailles bornées |
| SonarCloud | Optionnel (skip si secret absent) |

---

## 4. CI/CD

### CI (`.github/workflows/ci.yml`)

Jobs :
1. **quality** — ruff, pylint, mypy, bandit, pip-audit (informatif)
2. **test** — pytest avec seuil de couverture 80% bloquant
3. **sonar** — SonarCloud, skip silencieusement si `SONAR_TOKEN` absent
4. **docker-build** — Build et push de l'image vers GHCR (sur `main` et `dev`)

### CD (`.github/workflows/cd.yml`)

Volontairement minimal pour rester pédagogique :
1. **docker-smoke-test** — build l'image, lance le conteneur, curl `/api/health`
2. **terraform-validate** — `terraform fmt -check` + `terraform validate`

**Le déploiement Azure est manuel** (Terraform + Ansible — voir README).

---

## 5. Conteneurisation

| Pratique | Statut |
|---|---|
| Multi-stage build | ✅ |
| Utilisateur non-root (`appuser`) | ✅ |
| HEALTHCHECK sur `/api/health` | ✅ |
| Image alpine/slim minimale | ✅ (python:3.12-slim) |
| `.dockerignore` | ✅ |
| Image scan (Trivy) | ❌ (à ajouter) |

---

## 6. Monitoring & observabilité

| Brique | Outil | Statut |
|---|---|---|
| Métriques applicatives | prometheus_flask_exporter | ✅ |
| Scraping | Prometheus | ✅ |
| Visualisation | Grafana (dashboard provisionné) | ✅ |
| Logs structurés | JSON via logging | ✅ |
| Agrégation logs | Loki + Promtail | ✅ |
| Alerting | — | ❌ (à ajouter : Alertmanager) |

---

## 7. Infrastructure as Code

| Outil | Périmètre | Statut |
|---|---|---|
| Terraform | RG, VNet, Subnet, NSG, IP publique, VM Ubuntu | ✅ Validé en CI |
| Ansible | Install Docker, déploiement compose, monitoring | ✅ |
| State Terraform | Local (par défaut) | ⚠️ Voir limites |

---

## 8. Synthèse — Ce qui est automatisé / manuel

| Étape | Automatisé | Manuel |
|---|:-:|:-:|
| Lint, format, types, sécurité code | ✅ | |
| Tests + couverture | ✅ | |
| Build & push image Docker | ✅ | |
| Validation Terraform | ✅ | |
| Smoke test Docker | ✅ | |
| Provisioning Azure (Terraform apply) | | ✅ |
| Déploiement Ansible | | ✅ |
| Destruction Azure (Terraform destroy) | | ✅ |

---

## 9. Limites et améliorations possibles

Choix de **simplicité pédagogique** assumés. À renforcer pour un contexte de production :

- **Backend Terraform distant** (Azure Blob Storage) — actuellement local
- **Déploiement automatique** vers Azure — actuellement manuel par sécurité (éviter coûts)
- **SonarCloud obligatoire** — actuellement optionnel pour faciliter le fork du projet
- **pip-audit bloquant** — actuellement informatif (les CVE des deps évoluent quotidiennement et casseraient la CI sans rapport avec le code)
- **Trivy** (scan image Docker) et **hadolint** (lint Dockerfile) à ajouter en CI
- **Alertmanager** + règles d'alerte Prometheus
- **Restriction réseau** plus fine sur le NSG Azure
- **HTTPS** (Let's Encrypt) au lieu d'HTTP
- **PostgreSQL** au lieu de SQLite en production
- **Multi-environnements** (dev / staging / prod) via workspaces Terraform
- **Tests de charge** (k6, Locust)
- **Renovate / Dependabot** pour la mise à jour automatique des dépendances

---

## 10. Comment exécuter tous les contrôles localement

```bash
./scripts/quality_check.sh          # complet
./scripts/quality_check.sh --fast   # sans pip-audit ni radon
```

Ou individuellement, voir le tableau du [README](README.md#tests-et-qualité).
