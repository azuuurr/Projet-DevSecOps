# Plateforme de Gestion Académique Sécurisée

> Projet DevSecOps — Guardia Cybersecurity School — GCS2 2025-2026

Application web sécurisée de gestion académique (notes, classes, emplois du temps) développée avec Flask, MySQL, Docker et une pipeline CI/CD GitHub Actions.

## Stack Technique

- **Back-end** : Python 3.11 / Flask 3.1
- **Base de données** : MySQL 8.0
- **Front-end** : Jinja2 + Tailwind CSS
- **Conteneurisation** : Docker & Docker Compose
- **CI/CD** : GitHub Actions (Flake8, Semgrep, pip-audit, OWASP ZAP)

## Fonctionnalités

### Système RBAC (3 rôles)

| Rôle | Permissions |
|------|-------------|
| **Administrateur** | Gestion des utilisateurs, classes, matières, emplois du temps, attribution étudiants/professeurs |
| **Professeur** | Consultation classes attribuées, création d'évaluations, attribution et modification de notes |
| **Étudiant** | Consultation de ses propres notes et emploi du temps uniquement |

### Sécurité Applicative

- Hachage des mots de passe avec **bcrypt**
- Protection **CSRF** sur tous les formulaires (Flask-WTF)
- Validation et assainissement des entrées (WTForms + bleach)
- **Requêtes paramétrées** exclusivement (aucune concaténation SQL)
- Headers HTTP de sécurité via **Flask-Talisman** (CSP, X-Frame-Options, etc.)
- Gestion des sessions sécurisée (durée limitée, HTTPOnly, SameSite, régénération)
- Journalisation des accès non autorisés (403)

## Installation locale (XAMPP)

### Prérequis

- Python 3.11+
- XAMPP avec MySQL/MariaDB démarré
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-groupe/DevSecOps.git
cd DevSecOps

# 2. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
copy .env.example .env
# Modifier .env si nécessaire (mot de passe MySQL, etc.)

# 5. Initialiser et seeder la base de données
python seed_db.py

# 6. Lancer l'application
python run.py
```

L'application sera accessible sur **http://localhost:5000**

## Installation Docker

```bash
# Lancer tous les services
docker compose up -d --build

# L'application sera accessible sur http://localhost:5000
# MySQL sera accessible sur le port 3307
```

## Comptes de test

| Rôle | Utilisateur | Mot de passe |
|------|-------------|--------------|
| Admin | `admin` | `password123` |
| Professeur | `prof.martin` | `password123` |
| Professeur | `prof.bernard` | `password123` |
| Étudiant | `etudiant.durand` | `password123` |
| Étudiant | `etudiant.petit` | `password123` |
| Étudiant | `etudiant.moreau` | `password123` |
| Étudiant | `etudiant.leroy` | `password123` |
| Étudiant | `etudiant.roux` | `password123` |

## Structure du Projet

```
DevSecOps/
├── app/
│   ├── __init__.py          # App factory Flask + sécurité
│   ├── config.py            # Configuration dev/prod
│   ├── db.py                # Helper DB (requêtes paramétrées)
│   ├── auth/                # Blueprint authentification + RBAC
│   ├── admin/               # Blueprint administrateur
│   ├── professor/           # Blueprint professeur
│   ├── student/             # Blueprint étudiant
│   ├── templates/           # Templates Jinja2 + Tailwind
│   └── static/              # Fichiers statiques
├── sql/
│   ├── schema.sql           # Schéma de la base de données
│   └── seed.sql             # Données de test
├── .github/workflows/
│   └── ci-cd.yml            # Pipeline CI/CD
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── seed_db.py               # Script de seeding Python
├── run.py                   # Point d'entrée
└── README.md
```

## Pipeline CI/CD

La pipeline GitHub Actions se déclenche à chaque push/PR sur `main` :

1. **Flake8** — Lint et qualité du code Python
2. **Semgrep** — Analyse statique de sécurité (SAST)
3. **pip-audit** — Scan des dépendances vulnérables
4. **Docker Build** — Construction de l'image conteneurisée
5. **OWASP ZAP** — Scan dynamique automatisé (DAST)
6. **Deploy** — Déploiement via Docker Compose

## Auteurs

Groupe GCS2 — Guardia Cybersecurity School — 2025-2026
"# Projet-DevSecOps" 
