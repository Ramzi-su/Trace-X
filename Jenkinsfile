pipeline {
    agent any

    environment {
        IMAGE_NAME = "trace-x-app"
    }

    stages {
        // J'ai supprimé l'étape "Nettoyage" ici car elle effaçait ton code !
        
        // Étape 1 : Construction
        stage('Build Image') {
            steps {
                script {
                    echo "Construction de l'image..."
                    // AJOUT DE SUDO : Indispensable car l'user jenkins n'est pas configuré pour le rootless
                    sh "sudo podman build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        // Étape 2 : Test
        stage('Test') {
            steps {
                script {
                    echo "Lancement du test..."
                    // AJOUT DE SUDO ici aussi
                    sh "sudo podman run --rm --privileged ${IMAGE_NAME}:latest python --version"
                }
            }
        }
    }

    // Le nettoyage se fait TOUJOURS à la fin, qu'il y ait réussite ou échec
    post {
        always {
            cleanWs()
            echo "Nettoyage de l'espace de travail terminé."
        }
    }
}