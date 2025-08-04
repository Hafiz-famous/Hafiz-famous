# Utiliser Python 3.11
FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Créer le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer un utilisateur non-root
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Exposer le port
EXPOSE 5000

# Commande par défaut
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "run:app"]