pipeline {
    agent any

    environment {
        IMAGE_NAME = "trace-x-app"
        GOOGLE_API_KEY = "TA_CLE_ICI"
    }

    stages {
        stage('Build Image') {
            steps {
                script {
                    echo "🔨 Construction..."
                    // On utilise 'docker' au lieu de 'podman'
                    sh "sudo docker build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "🧪 Test..."
                    // Idem ici
                    sh "sudo docker run --rm --privileged ${IMAGE_NAME}:latest python --version"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo "🚀 Déploiement..."
                    try {
                        // On utilise 'docker-compose'
                        sh "sudo docker-compose down"
                    } catch (Exception e) {
                        echo "Rien à éteindre."
                    }
                    sh "sudo docker-compose up -d"
                }
            }
        }
    }

    post {
        always {
            echo "✅ Terminé."
        }
    }
}