/**
 * RH Platform - JavaScript principal
 */

// Configuration globale
const API_BASE_URL = '/api';
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Classe principale de l'application
class RHPlatform {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuth();
        this.initCharts();
    }

    setupEventListeners() {
        // Gestion de la connexion
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }

        // Gestion du pointage
        const punchButtons = document.querySelectorAll('.punch-button');
        punchButtons.forEach(button => {
            button.addEventListener('click', this.handlePunch.bind(this));
        });

        // Gestion des congés
        const leaveForms = document.querySelectorAll('.leave-form');
        leaveForms.forEach(form => {
            form.addEventListener('submit', this.handleLeaveRequest.bind(this));
        });

        // Gestion des validations
        const approveButtons = document.querySelectorAll('.approve-leave');
        approveButtons.forEach(button => {
            button.addEventListener('click', this.handleLeaveApproval.bind(this));
        });

        // Auto-refresh du token
        setInterval(() => {
            this.refreshToken();
        }, 14 * 60 * 1000); // Toutes les 14 minutes
    }

    // Gestion de l'authentification
    async handleLogin(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = {
            email: formData.get('email'),
            password: formData.get('password')
        };

        try {
            this.showLoading(event.target);
            
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem(TOKEN_KEY, result.access_token);
                localStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token);
                window.location.href = '/dashboard';
            } else {
                this.showError(result.message || 'Erreur de connexion');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
        } finally {
            this.hideLoading(event.target);
        }
    }

    async refreshToken() {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (!refreshToken) return;

        try {
            const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${refreshToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                localStorage.setItem(TOKEN_KEY, result.access_token);
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Erreur lors du refresh du token:', error);
        }
    }

    logout() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.location.href = '/login';
    }

    checkAuth() {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token && window.location.pathname !== '/login' && window.location.pathname !== '/') {
            window.location.href = '/login';
        }
    }

    // Gestion du pointage
    async handlePunch(event) {
        event.preventDefault();
        
        const button = event.target;
        const punchType = button.dataset.type;
        
        try {
            this.showLoading(button);
            
            const response = await this.apiCall('/timekeeping/punch', {
                method: 'POST',
                body: JSON.stringify({
                    type: punchType,
                    location: 'Bureau principal',
                    device: 'Web'
                })
            });

            if (response.ok) {
                this.showSuccess('Pointage enregistré avec succès');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                const result = await response.json();
                this.showError(result.message || 'Erreur lors du pointage');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
        } finally {
            this.hideLoading(button);
        }
    }

    // Gestion des congés
    async handleLeaveRequest(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = {
            type: formData.get('type'),
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date'),
            reason: formData.get('reason')
        };

        try {
            this.showLoading(event.target);
            
            const response = await this.apiCall('/leaves', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.showSuccess('Demande de congé envoyée avec succès');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                const result = await response.json();
                this.showError(result.message || 'Erreur lors de la demande');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
        } finally {
            this.hideLoading(event.target);
        }
    }

    async handleLeaveApproval(event) {
        event.preventDefault();
        
        const button = event.target;
        const leaveId = button.dataset.leaveId;
        const action = button.dataset.action;
        
        try {
            this.showLoading(button);
            
            const response = await this.apiCall(`/leaves/${leaveId}/${action}`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showSuccess(`Congé ${action === 'approve' ? 'approuvé' : 'rejeté'} avec succès`);
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                const result = await response.json();
                this.showError(result.message || 'Erreur lors de la validation');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
        } finally {
            this.hideLoading(button);
        }
    }

    // Appels API génériques
    async apiCall(endpoint, options = {}) {
        const token = localStorage.getItem(TOKEN_KEY);
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...defaultOptions,
            ...options
        });

        if (response.status === 401) {
            this.logout();
        }

        return response;
    }

    // Gestion des graphiques
    initCharts() {
        // Graphique de présence
        const attendanceChart = document.getElementById('attendanceChart');
        if (attendanceChart) {
            this.createAttendanceChart(attendanceChart);
        }

        // Graphique des heures supplémentaires
        const overtimeChart = document.getElementById('overtimeChart');
        if (overtimeChart) {
            this.createOvertimeChart(overtimeChart);
        }

        // Graphique des congés
        const leavesChart = document.getElementById('leavesChart');
        if (leavesChart) {
            this.createLeavesChart(leavesChart);
        }
    }

    createAttendanceChart(canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                datasets: [{
                    label: 'Taux de présence (%)',
                    data: [95, 98, 92, 96, 94, 0, 0],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    createOvertimeChart(canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven'],
                datasets: [{
                    label: 'Heures supplémentaires',
                    data: [2.5, 1.5, 3.0, 2.0, 1.0],
                    backgroundColor: '#ffc107'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    createLeavesChart(canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Congés payés', 'Congés maladie', 'Congés maternité', 'Autres'],
                datasets: [{
                    data: [15, 3, 0, 2],
                    backgroundColor: [
                        '#198754',
                        '#dc3545',
                        '#0dcaf0',
                        '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Utilitaires UI
    showLoading(element) {
        const originalText = element.innerHTML;
        element.innerHTML = '<span class="loading-spinner"></span> Chargement...';
        element.disabled = true;
        element.dataset.originalText = originalText;
    }

    hideLoading(element) {
        const originalText = element.dataset.originalText;
        if (originalText) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertContainer, container.firstChild);

        // Auto-dismiss après 5 secondes
        setTimeout(() => {
            alertContainer.remove();
        }, 5000);
    }

    // Mise à jour en temps réel
    startRealTimeUpdates() {
        setInterval(() => {
            this.updateDashboard();
        }, 30000); // Toutes les 30 secondes
    }

    async updateDashboard() {
        try {
            const response = await this.apiCall('/dashboard/stats');
            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
            }
        } catch (error) {
            console.error('Erreur lors de la mise à jour du dashboard:', error);
        }
    }

    updateDashboardStats(data) {
        // Mise à jour des statistiques affichées
        const statElements = document.querySelectorAll('[data-stat]');
        statElements.forEach(element => {
            const statName = element.dataset.stat;
            if (data[statName] !== undefined) {
                element.textContent = data[statName];
            }
        });
    }
}

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', () => {
    window.rhPlatform = new RHPlatform();
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RHPlatform;
}