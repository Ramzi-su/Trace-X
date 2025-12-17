document.addEventListener('DOMContentLoaded', function () {
    const socket = io();
    // Buttons
    const networkScanBtn = document.getElementById('networkScanBtn');
    const portScanBtn = document.getElementById('portScanBtn');
    const chatBtn = document.getElementById('chatBtn');
    // AJOUTER CECI :
    const shutdownBtn = document.getElementById('shutdownBtn');
    // UI Elements
    const resultsContainer = document.getElementById('results');
    const statusText = document.getElementById('statusText');
    const placeholder = document.getElementById('initial-placeholder');
    const targetInput = document.getElementById('targetInput');
    // Chat Elements
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');

    let discoveredHosts = [];
    let pendingScans = new Set();

    // --- Socket.IO Event Handlers ---
    socket.on('connect', () => {
        statusText.innerHTML = `<span class="text-success">Connecté au serveur. Prêt à scanner.</span>`;
    });

    socket.on('disconnect', () => {
        // 1. Message en bas de page
        statusText.innerHTML = `<span class="text-danger fw-bold">⚠️ Serveur éteint. Connexion perdue.</span>`;

        // 2. On arrête le spinner du bouton rouge et on le grise
        if (shutdownBtn) {
            shutdownBtn.innerHTML = '<i class="bi bi-power"></i> OFF'; // Change le texte
            shutdownBtn.classList.replace('btn-danger', 'btn-dark');   // Devient noir/gris
            shutdownBtn.disabled = true; // On ne peut plus cliquer
        }

        // 3. (Optionnel) On désactive les autres boutons pour éviter les erreurs
        networkScanBtn.disabled = true;
        portScanBtn.disabled = true;
        chatBtn.disabled = true;
        targetInput.disabled = true;
    });

    socket.on('status_update', (data) => {
        let levelClass = 'text-white';
        if (data.level === 'error') levelClass = 'text-danger';
        if (data.level === 'success') levelClass = 'text-success';
        if (data.level === 'warning') levelClass = 'text-warning';
        statusText.innerHTML = `<span class="${levelClass}">${data.msg}</span>`;
    });

    socket.on('host_discovered', (host) => {
        if (placeholder) placeholder.style.display = 'none';
        if (discoveredHosts.some(h => h.ip === host.ip)) return;

        discoveredHosts.push(host);
        portScanBtn.disabled = false;
        portScanBtn.classList.replace('btn-secondary', 'btn-info');

        const cardHtml = `
            <div class="col-md-6 col-lg-4" id="host-${host.ip.replace(/\./g, '-')}">
                <div class="card">
                    <div class="card-header fw-bold d-flex flex-wrap align-items-baseline">
                        <span class="me-2"><i class="bi bi-pc-display"></i> ${host.ip}</span>
                        <span class="badge bg-secondary text-wrap" id="type-${host.ip.replace(/\./g, '-')}">En attente</span>
                    </div>
                    <div class="card-body">
                        <p class="card-text mb-2"><strong>MAC:</strong> ${host.mac}<br><strong>Fabricant:</strong> ${host.vendor}</p>
                        <div id="ports-${host.ip.replace(/\./g, '-')}" class="mt-2"><small class="text-muted">Analyse des ports non effectuée.</small></div>
                    </div>
                </div>
            </div>`;
        resultsContainer.insertAdjacentHTML('beforeend', cardHtml);
    });

    socket.on('scan_result', (result) => {
        const hostData = discoveredHosts.find(h => h.ip === result.ip);
        const portsContainer = document.getElementById(`ports-${result.ip.replace(/\./g, '-')}`);

        // Assurer que l'hôte (dans les données) et sa carte (dans le DOM) existent avant de continuer.
        if (hostData && portsContainer) {
            // Mettre à jour les données de l'hôte pour le contexte de l'IA
            hostData.device_type = result.device_type;
            hostData.ports = result.ports;

            // Mettre à jour l'interface utilisateur (ce qui supprime le spinner)
            let portsHtml = '<h6>Ports Ouverts:</h6>';
            if (result.ports.length > 0) {
                portsHtml += '<ul class="list-group list-group-flush">';
                result.ports.forEach(p => {
                    portsHtml += `<li class="list-group-item bg-transparent d-flex justify-content-between"><span>${p.port}/tcp</span> <span class="text-muted">${p.service}</span></li>`;
                });
                portsHtml += '</ul>';
            } else {
                portsHtml = '<p class="text-muted">Aucun port commun ouvert.</p>';
            }
            portsContainer.innerHTML = portsHtml;

            const typeElement = document.getElementById(`type-${result.ip.replace(/\./g, '-')}`);
            if (typeElement) {
                typeElement.textContent = result.device_type;
                typeElement.classList.replace('bg-secondary', 'bg-primary');
            }

            // Logique de complétion robuste utilisant un Set
            if (pendingScans.has(result.ip)) {
                // Le message de fin global est géré par l'événement 'port_scan_complete'.
                pendingScans.delete(result.ip);
            }
        }
    });

    socket.on('port_scan_complete', () => {
        // Le serveur confirme la fin du cycle de scan. L'application est débloquée.
        statusText.innerHTML = `<span class="text-success">Analyse des ports terminée.</span>`;
        portScanBtn.disabled = false;
        targetInput.disabled = false;

        // On vérifie s'il reste des scans en attente et on met à jour leur état.
        pendingScans.forEach(ip => {
            const portsContainer = document.getElementById(`ports-${ip.replace(/\./g, '-')}`);
            if (portsContainer) {
                portsContainer.innerHTML = '<p class="text-warning small">Le résultat du scan pour cet hôte n\'a pas été reçu.</p>';
            }
        });
        pendingScans.clear();
    });

    socket.on('ai_response', (data) => {
        addMessageToChat(data.error ? `Erreur: ${data.error}` : data.response, 'ai');
        chatInput.disabled = false;
        chatInput.focus();
    });

    // --- User Action Handlers ---
    networkScanBtn.addEventListener('click', () => {
        // Réinitialisation de l'interface
        resultsContainer.innerHTML = '';
        if (placeholder) resultsContainer.appendChild(placeholder);
        placeholder.style.display = 'block';
        discoveredHosts = [];
        pendingScans.clear();
        targetInput.value = '';
        portScanBtn.disabled = true;
        portScanBtn.classList.replace('btn-info', 'btn-secondary');
        
        socket.emit('start_network_scan');
        networkScanBtn.disabled = true;
        setTimeout(() => networkScanBtn.disabled = false, 3000); // Anti-spam
    });

    targetInput.addEventListener('input', () => {
        if (targetInput.value.trim() !== '') {
            portScanBtn.disabled = false;
            portScanBtn.classList.replace('btn-secondary', 'btn-info');
        } else if (discoveredHosts.length === 0) {
            portScanBtn.disabled = true;
            portScanBtn.classList.replace('btn-info', 'btn-secondary');
        }
    });

    portScanBtn.addEventListener('click', () => {
        const singleTarget = targetInput.value.trim();
        if (singleTarget) {
            socket.emit('start_single_host_port_scan', { target: singleTarget });
            portScanBtn.disabled = true;
            targetInput.disabled = true;
        } else if (discoveredHosts.length > 0) {
            pendingScans.clear();
            // Met à jour l'UI pour montrer que le scan de ports est en cours
            discoveredHosts.forEach(host => {
                pendingScans.add(host.ip);
                const portsContainer = document.getElementById(`ports-${host.ip.replace(/\./g, '-')}`);
                if (portsContainer) {
                    portsContainer.innerHTML = `<div class="d-flex align-items-center"><div class="spinner-border spinner-border-sm text-info" role="status"></div><small class="ms-2">Analyse en cours...</small></div>`;
                }
            });
            socket.emit('start_port_scan', { hosts: discoveredHosts });
            portScanBtn.disabled = true;
        }
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        addMessageToChat(message, 'user');
        chatInput.disabled = true;
        
        socket.emit('chat_message', {
            message: message,
            scan_context: JSON.stringify(discoveredHosts, null, 2)
        });
        chatInput.value = '';
    });
    // ... les autres addEventListener ...

    shutdownBtn.addEventListener('click', () => {
        // Une petite confirmation pour ne pas éteindre par erreur
     if (confirm("Voulez-vous vraiment arrêter le serveur Trace-X ?")) {
        // On désactive le bouton pour éviter de cliquer deux fois
        shutdownBtn.disabled = true;
        shutdownBtn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
        
        // On envoie l'ordre au serveur
        socket.emit('shutdown_server');
        }
    });

    // --- Utility Functions ---
    function addMessageToChat(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `${sender}-message chat-message`;
    
    // Si c'est l'IA, on utilise marked pour transformer le texte en HTML
    if (sender === 'ai') {
        messageDiv.innerHTML = marked.parse(message);
    } else {
        // Pour l'utilisateur, on garde le texte brut (sécurité)
        messageDiv.textContent = message;
    }
    
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}
});