# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # 1. LE "NAVIR" (L'OS de la VM)
  # On utilise Ubuntu 22.04 car c'est le plus stable pour Docker
  config.vm.box = "bento/ubuntu-22.04"

  # 2. LE RÉSEAU (Mode Pont / Bridge)
  # La VM aura sa propre adresse IP. C'est VITAL pour le scan réseau.
  # Au démarrage, il te demandera quelle carte Wi-Fi utiliser.
  config.vm.network "public_network", bridge: "wlo1"

  # 3. LE CHARGEMENT (Dossier partagé)
  # Ton dossier Trace-X actuel sera accessible dans la VM sous /vagrant
  config.vm.synced_folder ".", "/vagrant"

  # 4. LE MOTEUR (RAM & CPU)
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "4096"  # 4 Go de RAM
    vb.cpus = 2         # 2 Cœurs
    vb.name = "Trace-X-VM"
  end

  # 5. L'INSTALLATION AUTOMATIQUE (Provisioning)
  # Ce script installe Docker et Docker Compose tout seul au 1er démarrage.
  config.vm.provision "shell", inline: <<-SHELL
    echo "🛠️ Démarrage de l'installation de Docker..."
    
    # Mise à jour des paquets
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release

    # Ajout de la clé officielle Docker
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Ajout du dépôt Docker
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Installation de Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-compose

    # Configuration des droits (pour utiliser docker sans sudo)
    usermod -aG docker vagrant
    
    echo "✅ Installation terminée ! La VM est prête."
  SHELL
end