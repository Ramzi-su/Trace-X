pipeline {
    agent any

    stages {
        stage('1. Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/Ramzi-su/Trace-X.git'
            }
        }

        stage('2. Démarrage VM & Application') {
            steps {
                script {
                    echo "🚀 Démarrage de la VM..."
                    sh 'vagrant destroy -f || true'
                    sh 'vagrant up'

                    echo "🔨 Construction et Lancement de Trace-X..."
                    // C'EST ICI QUE CA MANQUAIT : On construit et on lance !
                    // 1. cd /vagrant : On va dans le dossier
                    // 2. docker build : On fabrique l'image locale
                    // 3. docker-compose up : On lance les conteneurs
                    sh 'vagrant ssh -c "cd /vagrant && docker build -t trace-x-app:latest . && docker-compose up -d"'
                }
            }
        }

        stage('3. Tests d\'Intégration') {
            steps {
                script {
                    echo "🧪 Tests en cours..."
                    
                    // On attend 15 secondes que le serveur soit bien réveillé
                    sh 'sleep 15'

                    // Test 1 : Est-ce que le conteneur tourne ?
                    sh 'vagrant ssh -c "docker ps | grep tracex_server"'
                    
                    // Test 2 : Est-ce que le site répond "200 OK" ?
                    sh 'vagrant ssh -c "curl -f http://localhost:5000"'
                }
            }
        }
    }

    post {
        always {
            echo "🧹 Nettoyage..."
            sh 'vagrant destroy -f'
        }
        success {
            echo "✅ SUCCÈS : L'application fonctionne parfaitement !"
        }
        failure {
            echo "❌ ÉCHEC : Quelque chose a cassé."
        }
    }
}