#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# quality_check.sh — chaîne complète de qualité de code
#
# Lance : ruff, pylint, mypy, pytest+coverage, bandit, radon, pip-audit
# Usage : ./scripts/quality_check.sh [--fast]
#   --fast : saute pip-audit (réseau) et radon (complexité)
# ─────────────────────────────────────────────────────────────
set -u
set -o pipefail

FAST=0
[[ "${1:-}" == "--fast" ]] && FAST=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_DIR="app"
TESTS_DIR="tests"

# Codes couleur
G="\033[32m"; R="\033[31m"; Y="\033[33m"; B="\033[34m"; N="\033[0m"

EXIT_CODE=0
declare -a FAILED_STEPS=()

run_step() {
    local name="$1"; shift
    echo -e "\n${B}== ${name} ==${N}"
    if "$@"; then
        echo -e "${G}[OK] ${name}${N}"
    else
        echo -e "${R}[FAIL] ${name}${N}"
        FAILED_STEPS+=("$name")
        EXIT_CODE=1
    fi
}

# 1. Ruff (lint + format check)
run_step "ruff (lint)"        ruff check "$APP_DIR" "$TESTS_DIR"
run_step "ruff (format)"      ruff format --check "$APP_DIR" "$TESTS_DIR"

# 2. Pylint (qualité)
run_step "pylint"             pylint "$APP_DIR" --rcfile=.pylintrc

# 3. Mypy (types)
run_step "mypy"               mypy --config-file=mypy.ini

# 4. Pytest + couverture (seuil dans pyproject.toml)
run_step "pytest + coverage"  pytest --cov="$APP_DIR" --cov-report=term-missing --cov-fail-under=80

# 5. Bandit (sécurité)
run_step "bandit (security)"  bandit -r "$APP_DIR" -c pyproject.toml -q

# 6. Radon (complexité)
if [[ $FAST -eq 0 ]]; then
    run_step "radon (cc)"     radon cc "$APP_DIR" -a -s -nb
    run_step "radon (mi)"     radon mi "$APP_DIR" -nb
fi

# 7. Pip-audit (CVE deps)
if [[ $FAST -eq 0 ]]; then
    run_step "pip-audit"      pip-audit --strict
fi

echo ""
echo "════════════════════════════════════════"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${G}[SUCCESS] Tous les checks de qualite ont passe.${N}"
else
    echo -e "${R}[FAILURE] Etapes en echec :${N}"
    for s in "${FAILED_STEPS[@]}"; do
        echo -e "  - ${Y}${s}${N}"
    done
fi
echo "════════════════════════════════════════"
exit $EXIT_CODE
