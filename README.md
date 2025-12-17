# Trace-X 📡

**Trace-X** est un outil avancé de découverte réseau et de scan de ports, alliant la puissance de Python à l'intelligence artificielle. Il offre une double interface : une ligne de commande (CLI) pour les utilisateurs avancés et une interface Web moderne et réactive pour une visualisation en temps réel.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

##  Fonctionnalités

- **Découverte Réseau (ARP Scan)** : Identifie rapidement tous les appareils connectés à votre réseau local (IP, MAC, Fabricant).
- **Scan de Ports Multi-threadé** : Analyse rapide des ports ouverts (TCP) sur les cibles identifiées.
- **Identification des Appareils** : Tente de déterminer le type d'appareil (Routeur, PC, Imprimante, IoT) via des heuristiques basées sur les ports et l'adresse MAC.
- **Assistant IA (Gemini Pro)** : Discutez avec une IA intégrée qui analyse les résultats de vos scans pour fournir des conseils de sécurité et des explications techniques.
- **Double Interface** :
  - **Web (FastAPI + SocketIO)** : Tableau de bord temps réel, chat interactif.
  - **CLI (Terminal)** : Mode console robuste avec barres de progression.

## 🛠️ Prérequis

- **Système d'exploitation** : Linux (recommandé pour Scapy) ou macOS.
- **Python** : Version 3.8 ou supérieure.
- **Privilèges** : Accès `root` (sudo) requis pour l'envoi de paquets ARP et les scans bas niveau.
- **Clé API Google** : Pour activer les fonctionnalités d'IA (Gemini).

## 📦 Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/votre-username/Trace-X.git
   cd Trace-X
   ```

2. **Créer un environnement virtuel (recommandé)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Créez un fichier `.env` à la racine du projet pour stocker votre clé API Google (nécessaire pour le chat IA).

```bash
# .env
GOOGLE_API_KEY="votre_clé_api_google_ici"
```

> **Note** : Sans cette clé, les fonctionnalités de scan fonctionneront, mais pas l'assistant IA.

## 🖥️ Utilisation

### Mode Interface Web (Recommandé)

Lancez le serveur web FastAPI. L'application sera accessible sur `http://127.0.0.1:5000`.

```bash
sudo .venv/bin/uvicorn app:app --host 127.0.0.1 --port 5000
```
*Note : `sudo` est nécessaire pour permettre à Scapy de scanner le réseau.*

### Mode Ligne de Commande (CLI)

Pour une utilisation rapide directement dans le terminal :

```bash
sudo python3 main.py
```
Suivez ensuite les instructions du menu interactif.

## 📂 Structure du Projet

```
Trace-X/
├── app.py              # Serveur Web (FastAPI + SocketIO)
├── main.py             # Point d'entrée pour le mode CLI
├── network_scanner.py  # Logique de scan ARP (Scapy)
├── port_scanner.py     # Logique de scan de ports (Socket + Threading)
├── utils.py            # Utilitaires (Réseau, OUI Database, Identification)
├── requirements.txt    # Dépendances Python
├── static/             # Fichiers statiques (JS, CSS)
│   └── script.js       # Logique Frontend
└── templates/          # Templates HTML
    └── index.html
```

## ⚠️ Avertissement Légal

**Trace-X** est un outil conçu à des fins éducatives et pour l'administration réseau légitime.
L'utilisation de ce scanner sur un réseau sans l'autorisation explicite de son propriétaire peut être illégale. L'auteur décline toute responsabilité quant à une mauvaise utilisation de cet outil.

## 👤 Auteur

**Moulahi Ramzi**

---
*Développé avec passion pour la cybersécurité et l'automatisation.*