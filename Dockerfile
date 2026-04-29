# ── Build stage ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Installer les dépendances dans un répertoire isolé
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────
FROM python:3.12-slim

# Créer un utilisateur non-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copier uniquement les dépendances installées depuis le builder
COPY --from=builder /install /usr/local

# Copier le code applicatif
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup templates/ ./templates/
COPY --chown=appuser:appgroup run.py .

# Répertoire persistant pour la base SQLite
RUN mkdir -p /app/instance && chown appuser:appgroup /app/instance

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
