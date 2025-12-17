pipeline {
    agent any

    environment {
        IMAGE_NAME = "trace-x-app"
        // Remplace par ta vraie clé ou configure-la dans les secrets Jenkins plus tard
        GOOGLE_API_KEY = "TA_CLE_GOOGLE_ICI_OU_LAISSE_VIDE_POUR_TEST"
    }

    stages {
        stage('Build Image') {
            steps {
                script {
                    echo "🔨 Construction de l'image..."
                    sh "sudo podman build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "🧪 Test de démarrage..."
                    sh "sudo podman run --rm --privileged ${IMAGE_NAME}:latest python --version"
                }
            }
        }

        // --- C'est ici que la magie opère (CD) ---
        stage('Deploy') {
            steps {
                script {
                    echo "🚀 Déploiement en cours..."
                    // 1. On éteint les anciens conteneurs s'ils existent
                    try {
                        sh "sudo podman-compose down"
                    } catch (Exception e) {
                        echo "Rien à éteindre, on continue."
                    }
                    
                    // 2. On lance les nouveaux (en mode détaché -d)
                    sh "sudo podman-compose up -d"
                }
            }
        }
    }

    post {
        always {
            // Note: On n'efface PAS l'espace de travail (cleanWs) tout de suite
            // car podman-compose a besoin du fichier docker-compose.yml qui est dedans !
            echo "✅ Déploiement terminé."
        }
    }
}