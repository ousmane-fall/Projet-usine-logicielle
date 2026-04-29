# Architecture TaskFlow

## Vue d'ensemble

TaskFlow est une API REST de gestion de tâches servant de support à une usine logicielle complète.

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub                                │
│  ┌──────────┐   push/PR   ┌──────────────────────────────┐  │
│  │   Dev    │ ──────────► │   GitHub Actions (CI/CD)     │  │
│  │  branch  │             │  lint → test → sonar → build  │  │
│  └──────────┘             └───────────────┬──────────────┘  │
└──────────────────────────────────────────┼─────────────────┘
                                           │ deploy (Ansible)
                                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Serveur / Docker                         │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  TaskFlow   │    │  Prometheus  │    │    Grafana    │  │
│  │  Flask API  │───►│  (métriques) │───►│  (dashboards) │  │
│  │  :5000      │    │  :9090       │    │  :3000        │  │
│  └──────┬──────┘    └──────────────┘    └───────────────┘  │
│         │ logs                                   ▲          │
│         ▼                                        │          │
│  ┌─────────────┐    ┌──────────────┐             │          │
│  │  Promtail   │───►│     Loki     │─────────────┘          │
│  │  (collecte) │    │  :3100       │                        │
│  └─────────────┘    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Couverture des 11 chapitres

| # | Chapitre | Implémentation |
|---|---|---|
| 01-02 | Usine Logicielle | Ce document + README — pipeline complet de A à Z |
| 03 | GitOps | Branches `main`/`dev`/`feature/*`, PR template, commits conventionnels |
| 04-05 | GitHub Actions | `.github/workflows/ci.yml` + `cd.yml` |
| 06-07 | Tests Automatisés | `tests/unit/` + `tests/integration/`, coverage ≥ 80% |
| 08 | Qualité du code | `ruff` (lint), SonarCloud (analyse statique), badge coverage |
| 09 | Monitoring | Prometheus (métriques) + Grafana (dashboards) |
| 10 | Logs | Loki (stockage) + Promtail (collecte Docker) + dashboard Grafana |
| 11 | IaC | `infra/terraform/` (Docker provider) + `infra/ansible/` (configuration) |

## Flux CI/CD

```
feature/* ──► dev ──────────────────────────────► main
                │                                   │
                │  push                             │ push
                ▼                                   ▼
          CI: lint+test+sonar              CI + docker build+push
                                                    │
                                                    ▼
                                          CD: Ansible deploy
```

## Stack technique

- **App** : Python 3.12 / Flask 3 / SQLAlchemy / SQLite
- **Conteneurisation** : Docker / Docker Compose
- **CI/CD** : GitHub Actions
- **Qualité** : ruff, SonarCloud, pytest-cov
- **Monitoring** : Prometheus + Grafana
- **Logs** : Loki + Promtail
- **IaC** : Terraform (Docker provider) + Ansible
