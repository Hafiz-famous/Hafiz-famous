# Plateforme de Gestion RH - Pointage et Analyse

## 🎯 Vue d'ensemble

Plateforme complète de gestion des ressources humaines avec pointage, suivi des congés, analyse des performances et calcul des coûts salariaux.

## 🏗️ Architecture Technique

### Stack Technologique
- **Backend**: Python 3.11+, Flask, SQLAlchemy, Alembic
- **Base de données**: PostgreSQL
- **Frontend**: HTML5, CSS3, Bootstrap 5, Jinja2
- **Graphiques**: Chart.js
- **Sécurité**: JWT, RBAC, HTTPS
- **Tests**: pytest, Cypress
- **CI/CD**: GitHub Actions

### Architecture Modulaire
```
rh-platform/
├── app/                    # Application Flask
│   ├── __init__.py        # Configuration Flask
│   ├── models/            # Modèles SQLAlchemy
│   ├── routes/            # Blueprints Flask
│   ├── schemas/           # Schémas de validation
│   ├── services/          # Logique métier
│   ├── templates/         # Templates Jinja2
│   └── static/            # Assets (CSS, JS, images)
├── migrations/            # Migrations Alembic
├── tests/                 # Tests unitaires et d'intégration
├── docs/                  # Documentation
├── requirements.txt       # Dépendances Python
├── config.py             # Configuration
└── run.py                # Point d'entrée
```

## 🚀 Installation et Démarrage

### Prérequis
- Python 3.11+
- PostgreSQL 13+
- Node.js (pour les tests frontend)

### Installation
```bash
# Cloner le projet
git clone <repository-url>
cd rh-platform

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configuration de la base de données
export DATABASE_URL="postgresql://user:password@localhost/rh_platform"
# ou créer un fichier .env

# Migrations
flask db upgrade

# Lancer l'application
python run.py
```

## 📊 Fonctionnalités

### 1. Gestion des Pointages
- Pointage arrivée/départ
- Gestion des retards
- Calcul automatique des heures supplémentaires
- Validation par les managers

### 2. Gestion des Congés
- Demande de congés
- Workflow de validation
- Historique des congés
- Calcul des soldes

### 3. Analyse des Performances
- Tableau de bord global
- Métriques par département
- Employé du mois
- Indicateurs de rentabilité RH

### 4. Calcul des Coûts
- Coûts salariaux par département
- Analyse des heures supplémentaires
- Reporting financier

## 🔐 Sécurité

- Authentification JWT
- Gestion des rôles RBAC
- Validation des données
- Journalisation des actions
- Protection CSRF
- Headers de sécurité

## 🧪 Tests

```bash
# Tests backend
pytest tests/

# Tests frontend
npm test

# Tests d'intégration
pytest tests/integration/
```

## 📈 Monitoring

- Logs structurés
- Métriques de performance
- Alertes automatiques
- Sauvegarde automatique

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commiter les changements
4. Pousser vers la branche
5. Créer une Pull Request

## 📄 Licence

MIT License - voir LICENSE pour plus de détails.
