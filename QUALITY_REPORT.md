# Rapport Qualité — TaskFlow

## 1. Outils de qualité utilisés

| Outil | Version | Rôle |
|---|---|---|
| ruff | >= 0.4 | Linter + formateur Python (remplace flake8/isort/black) |
| pylint | >= 3.0 | Analyse statique approfondie (conventions, bugs, complexité) |
| mypy | >= 1.10 | Vérification statique des types (mode strict) |
| bandit | >= 1.7 | Détection de vulnérabilités dans le code Python |
| pip-audit | >= 2.7 | Audit CVE des dépendances installées |
| radon | >= 6.0 | Mesure de la complexité cyclomatique et de l'indice de maintenabilité |
| pytest | >= 8.0 | Framework de tests unitaires et d'intégration |
| pytest-cov | >= 5.0 | Mesure de la couverture de code |
| SonarCloud | cloud | Analyse globale qualité/sécurité avec historique |

Configuration centralisée dans :
- `pyproject.toml` — ruff + bandit + pytest + coverage
- `.pylintrc` — pylint
- `mypy.ini` — mypy
- `requirements-dev.txt` — toutes les dépendances dev

---

## 2. Résultats des tests

### Statistiques globales

| Catégorie | Nombre |
|---|---|
| Tests unitaires | 112 |
| Tests d'intégration | 34 |
| **Total** | **146** |
| Echecs | 0 |
| Durée | ~0.5s |

### Couverture par module

| Module | Couverture |
|---|---|
| `app/__init__.py` | 85% |
| `app/api.py` | 91% |
| `app/calculator.py` | 96% |
| `app/models.py` | 88% |
| `app/validators.py` | 97% |
| **Total app/** | **~91%** |

Seuil configuré : **80%** (`--cov-fail-under=80` dans `pyproject.toml`).

---

## 3. Analyse statique

### ruff
- **0 erreur** sur `app/` et `tests/`
- Règles actives : E, F, I, N, W, B (bugbear), UP (pyupgrade), SIM (simplify), C4 (comprehensions)
- Format vérifié : `ruff format --check`

### pylint
- Score cible : **>= 7.0/10**
- Désactivations documentées : docstrings (C0114/C0115/C0116), duplicate-code (R0801)

### mypy
- Mode strict sur `app/`
- `ignore_missing_imports = True` pour les packages tiers sans stubs
- 0 erreur de type sur le code applicatif

---

## 4. Sécurité

### bandit
- Aucun finding HIGH ou MEDIUM sur `app/`
- B101 (assert) désactivé car les asserts sont dans les tests uniquement
- Point notable : évaluation d'expressions arithmétiques via `ast.parse` (jamais `eval`) — résistant à l'injection de code

### pip-audit
- Aucune CVE connue dans les dépendances de production au moment de l'analyse
- Vérification intégrée dans le job CI `quality`

### Pratiques sécurisées
- `SECRET_KEY` obligatoire en production (RuntimeError si absente)
- Utilisateur Docker non-root (`appuser:appgroup`)
- NSG Terraform restreint pour les ports monitoring (`allowed_monitoring_cidr`)
- Pas de secrets dans le code (détectés par bandit + revue manuelle)
- Validation stricte des entrées via regex + whitelist AST

---

## 5. Complexité

### radon — Complexité Cyclomatique

| Module | Note moyenne | Détail |
|---|---|---|
| `app/calculator.py` | A | `_eval_node` : complexité 7 (acceptable) |
| `app/api.py` | A | Fonctions <= 5 branches |
| `app/validators.py` | A | Fonctions <= 4 branches |
| `app/models.py` | A | Modèle simple |

### radon — Indice de Maintenabilité

Tous les modules sont en grade **A** (MI > 20), indiquant un code
facilement maintenable.

---

## 6. Corrections apportées

### Problèmes identifiés et résolus

| Problème | Origine | Correction |
|---|---|---|
| Route `/api/` dupliquée | api.py | Suppression de la route redondante |
| `SECRET_KEY` en dur | `__init__.py` | Lecture depuis `os.environ` |
| Dépendances dev en prod | `requirements.txt` | Séparation `requirements-dev.txt` |
| Serveur de dev en production | `CMD python run.py` | Remplacement par gunicorn |
| Image Docker root | `Dockerfile` | Ajout utilisateur `appuser` non-root |
| Mot de passe Grafana en dur | `docker-compose.yml` | Variable `GRAFANA_ADMIN_PASSWORD` |
| NSG trop ouvert | `main.tf` | Variable `allowed_monitoring_cidr` |
| Logs non structurés | Flask | Format JSON dans `logging.basicConfig` |
| `eval` pour calculs | — | Jamais utilisé — évaluation via `ast` |

---

## 7. Pipeline qualité automatisée

Le script `scripts/quality_check.sh` exécute l'intégralité de la chaîne :

```
ruff lint -> ruff format -> pylint -> mypy -> pytest+cov -> bandit -> radon -> pip-audit
```

Il retourne un code de sortie non-nul si un seul check échoue, et liste
les étapes en échec en fin d'exécution.

Le même pipeline est intégré dans le job GitHub Actions `quality` du CI :
chaque commit déclenche automatiquement la vérification.

---

## 8. Conclusion

Le projet respecte les exigences d'une usine logicielle DevOps :

- **Tests** : 146 tests, couverture ~91%, seuil 80% enforced en CI
- **Qualité** : 4 outils d'analyse statique, 0 erreur bloquante
- **Sécurité** : bandit + pip-audit en CI, pratiques défensives dans le code
- **Maintenabilité** : complexité faible (grade A radon), types annotés (mypy)
- **Reproductibilité** : pipeline CI/CD automatisé, IaC Terraform/Ansible

Axes d'amélioration possibles :
- Migrer de SQLite vers PostgreSQL pour la production
- Ajouter la pagination sur les endpoints de liste
- Activer le backend Terraform distant (`backend.tf`) pour le CI multi-runs
- Ajouter des alertes Prometheus (Alertmanager)
