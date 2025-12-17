pipeline {
    agent any

    stages {
        stage('1. Checkout Code') {
            steps {
                // Jenkins récupère la dernière version de ton code
                git branch: 'main', url: 'https://github.com/Ramzi-su/Trace-X.git'
            }
        }

        stage('2. Nettoyage & Démarrage VM') {
            steps {
                script {
                    echo " Démarrage de l'environnement de test..."
                    // On s'assure qu'aucune vieille VM ne traîne
                    sh 'vagrant destroy -f || true'
                    // On lance la VM (ça prendra quelques minutes la première fois)
                    sh 'vagrant up'
                }
            }
        }

        stage('3. Tests d\'Intégration') {
            steps {
                script {
                    echo "🧪 Lancement des tests DANS la VM..."
                    
                    // Test 1 : Vérifier que Docker a bien lancé les conteneurs
                    sh 'vagrant ssh -c "docker ps | grep tracex_server"'
                    
                    // Test 2 : Vérifier que le site répond (Code HTTP 200)
                    // On attend 15s que le serveur Python démarre bien
                    sh 'vagrant ssh -c "sleep 15 && curl -f http://localhost:5000"'
                }
            }
        }
    }

    post {
        // Cette partie s'exécute TOUJOURS, même si ça plante
        always {
            echo " Nettoyage : Destruction de la VM de test..."
            sh 'vagrant destroy -f'
        }
        success {
            echo " Le déploiement et les tests sont validés."
        }
        failure {
            echo "quelque chose s'est mal passé."
        }
    }
}