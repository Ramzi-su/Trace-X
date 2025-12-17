# Image de base Python légère
FROM python:3.9-slim

# Installation des dépendances système (OBLIGATOIRE pour Scapy/Netifaces)
RUN apt-get update && apt-get install -y \
    gcc \
    libpcap-dev \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Dossier de travail
WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .
