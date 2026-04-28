#!/bin/bash
# ─────────────────────────────────────────────────────────────
# setup-secrets.sh
# Configure automatiquement tous les secrets GitHub du projet
# Prérequis : az CLI + gh CLI installés et connectés
#   az login
#   gh auth login
# ─────────────────────────────────────────────────────────────

set -e

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
  echo "[ERROR] Impossible de détecter le repo. Lance 'gh auth login' d'abord."
  exit 1
fi
echo "[OK] Repo détecté : $REPO"

# ── 1. Clé SSH ────────────────────────────────────────────────
SSH_KEY_PATH="$HOME/.ssh/id_rsa"
if [ ! -f "$SSH_KEY_PATH" ]; then
  echo "[INFO] Génération d'une paire de clés SSH..."
  ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N ""
fi
echo "[OK] Clés SSH prêtes"

gh secret set VM_SSH_PUBLIC_KEY  --repo "$REPO" < "${SSH_KEY_PATH}.pub"
gh secret set VM_SSH_PRIVATE_KEY --repo "$REPO" < "$SSH_KEY_PATH"
echo "[OK] Secrets SSH ajoutés"

# ── 2. Service Principal Azure ────────────────────────────────
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "[INFO] Subscription Azure : $SUBSCRIPTION_ID"

echo "[INFO] Création du Service Principal Azure (taskflow-sp)..."
SP_JSON=$(az ad sp create-for-rbac \
  --name "taskflow-sp" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --output json)

CLIENT_ID=$(echo "$SP_JSON"     | python3 -c "import sys,json; print(json.load(sys.stdin)['appId'])")
CLIENT_SECRET=$(echo "$SP_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")
TENANT_ID=$(echo "$SP_JSON"     | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant'])")

gh secret set AZURE_CLIENT_ID       --repo "$REPO" --body "$CLIENT_ID"
gh secret set AZURE_CLIENT_SECRET   --repo "$REPO" --body "$CLIENT_SECRET"
gh secret set AZURE_SUBSCRIPTION_ID --repo "$REPO" --body "$SUBSCRIPTION_ID"
gh secret set AZURE_TENANT_ID       --repo "$REPO" --body "$TENANT_ID"
echo "[OK] Secrets Azure ajoutés"

# ── 3. SonarCloud ─────────────────────────────────────────────
echo ""
echo "[INFO] SonarCloud"
echo "   -> Va sur https://sonarcloud.io, génère un token, puis colle-le :"
read -r -p "   SONAR_TOKEN : " SONAR_TOKEN
if [ -n "$SONAR_TOKEN" ]; then
  gh secret set SONAR_TOKEN --repo "$REPO" --body "$SONAR_TOKEN"
  echo "[OK] SONAR_TOKEN ajouté"
else
  echo "[SKIP] SONAR_TOKEN ignoré (tu pourras l'ajouter plus tard)"
fi

# ── Résumé ────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
echo "[OK] Tous les secrets sont configurés !"
echo "   Repo : https://github.com/$REPO/settings/secrets/actions"
echo ""
echo "   Prochaine étape :"
echo "   -> Mets à jour sonar-project.properties avec ton org SonarCloud"
echo "   -> git push sur main pour déclencher le pipeline"
echo "════════════════════════════════════════"
