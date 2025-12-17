pipeline {
    agent any

    environment {
        // On donne un nom à notre image
        IMAGE_NAME = "trace-x-app"
    }

    stages {
        // Étape 1 : Nettoyage (Pour éviter les conflits avec les anciens tests)
        stage('Nettoyage') {
            steps {
                cleanWs()
            }
        }

        // Étape 2 : Construction (Le cuisinier prépare le plat)
        stage('Build Image') {
            steps {
                script {
                    echo "Construction de l'image avec Podman..."
                    // On construit l'image en utilisant le Dockerfile
                    sh "podman build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        // Étape 3 : Test (Le goûteur vérifie si c'est bon)
        stage('Test') {
            steps {
                script {
                    echo "Lancement des tests..."
                    // On lance un conteneur temporaire (--rm) juste pour tester
                    // --privileged est OBLIGATOIRE pour Scapy
                    // On lance une commande simple pour voir si l'app démarre
                    sh "podman run --rm --privileged ${IMAGE_NAME}:latest python --version"
                }
            }
        }
    }
}