#!/bin/bash

# Script de démarrage pour RH Platform
# Usage: ./setup.sh [dev|prod]

set -e

echo "🚀 Installation de RH Platform..."

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérification de PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Création de l'environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
echo "📥 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Configuration de l'environnement
if [ "$1" = "prod" ]; then
    echo "🔧 Configuration pour la production..."
    cp .env.example .env
    echo "⚠️  Veuillez modifier le fichier .env avec vos paramètres de production"
else
    echo "🔧 Configuration pour le développement..."
    cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@localhost/rh_platform
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=5000
EOF
fi

# Création de la base de données
echo "🗄️  Configuration de la base de données..."
if ! psql -lqt | cut -d \| -f 1 | grep -qw rh_platform; then
    echo "Création de la base de données rh_platform..."
    createdb rh_platform
else
    echo "Base de données rh_platform existe déjà"
fi

# Initialisation de l'application
echo "🔧 Initialisation de l'application..."
python run.py init

echo "✅ Installation terminée !"
echo ""
echo "📋 Pour démarrer l'application :"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "🌐 L'application sera accessible sur : http://localhost:5000"
echo "👤 Compte administrateur : admin@rh-platform.com / Admin123!"
echo ""
echo "📚 Documentation :"
echo "   - API : http://localhost:5000/api/docs"
echo "   - Collection Postman : docs/API_POSTMAN_COLLECTION.json"
echo ""
echo "🐳 Pour utiliser Docker :"
echo "   docker-compose up -d"