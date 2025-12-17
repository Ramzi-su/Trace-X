pipeline {
    agent any

    environment {
        IMAGE_NAME = "trace-x-app"
        // Configure ta clé API ici ou laisse vide pour tester
        GOOGLE_API_KEY = "TA_CLE_GOOGLE_ICI"
    }

    stages {
        stage('Build Image') {
            steps {
                script {
                    echo "🔨 Construction avec Docker (Sans Cache)..."
                    // 👇 AJOUT DE --no-cache ICI
                    sh "sudo docker build --no-cache -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "🧪 Test de démarrage..."
                    sh "sudo docker run --rm --privileged ${IMAGE_NAME}:latest python --version"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo "🚀 Déploiement avec Compose..."
                    try {
                        // On éteint proprement avant de relancer
                        sh "sudo docker-compose down"
                    } catch (Exception e) {
                        echo "Première fois : rien à éteindre."
                    }
                    // On lance tout en arrière-plan (-d)
                    sh "sudo docker-compose up -d"
                }
            }
        }
    }

    post {
        always {
            echo "✅ Pipeline terminé."
        }
    }
}