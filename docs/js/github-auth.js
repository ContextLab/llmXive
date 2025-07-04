// GitHub Authentication with Personal Access Token
class GitHubAuth {
    constructor() {
        this.token = localStorage.getItem('github_pat');
        this.user = JSON.parse(localStorage.getItem('github_user') || 'null');
        this.apiBase = 'https://api.github.com';
    }
    
    // Check if authenticated
    isAuthenticated() {
        return !!this.token && !!this.user;
    }
    
    // Get user info
    getUser() {
        return this.user;
    }
    
    // Get auth headers
    getAuthHeaders() {
        if (!this.token) return {};
        return {
            'Authorization': `Bearer ${this.token}`,
            'Accept': 'application/vnd.github.v3+json'
        };
    }
    
    // Show login modal
    async login() {
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = `
            <div class="auth-modal-content">
                <button class="modal-close" onclick="window.githubAuth.closeAuthModal()">
                    <i class="fas fa-times"></i>
                </button>
                <h3><i class="fab fa-github"></i> GitHub Authentication</h3>
                
                <div class="auth-tabs">
                    <button class="tab-btn active" onclick="window.githubAuth.showTab('token')">
                        Personal Access Token
                    </button>
                    <button class="tab-btn" onclick="window.githubAuth.showTab('help')">
                        Help
                    </button>
                </div>
                
                <div id="tokenTab" class="tab-content active">
                    <p>Enter your GitHub Personal Access Token to enable all features:</p>
                    <input type="password" id="patInput" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" class="pat-input">
                    <button onclick="window.githubAuth.authenticateWithToken()" class="btn-primary">
                        <i class="fas fa-sign-in-alt"></i> Authenticate
                    </button>
                    <p class="auth-note">
                        Your token is stored locally and never sent to any server except GitHub.
                    </p>
                </div>
                
                <div id="helpTab" class="tab-content">
                    <h4>How to create a Personal Access Token:</h4>
                    <ol>
                        <li>Go to <a href="https://github.com/settings/tokens/new" target="_blank">GitHub Token Settings</a></li>
                        <li>Give it a name (e.g., "llmXive Dashboard")</li>
                        <li>Select expiration (recommend 90 days)</li>
                        <li>Select scope: <code>public_repo</code></li>
                        <li>Click "Generate token"</li>
                        <li>Copy the token and paste it above</li>
                    </ol>
                    <div class="auth-security">
                        <i class="fas fa-lock"></i>
                        <p>Your token is stored securely in your browser's local storage and is only used to communicate with GitHub's API.</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Focus input
        setTimeout(() => {
            document.getElementById('patInput')?.focus();
        }, 100);
        
        // Handle enter key
        document.getElementById('patInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.authenticateWithToken();
            }
        });
    }
    
    // Show tab
    showTab(tabName) {
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tabName.toLowerCase()));
        });
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id.toLowerCase().includes(tabName));
        });
    }
    
    // Authenticate with token
    async authenticateWithToken() {
        const input = document.getElementById('patInput');
        const token = input.value.trim();
        
        if (!token) {
            this.showError('Please enter a token');
            return;
        }
        
        // Show loading
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
        
        try {
            // Test token by fetching user info
            const response = await fetch(`${this.apiBase}/user`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Invalid token');
            }
            
            const user = await response.json();
            
            // Save token and user
            this.token = token;
            this.user = user;
            localStorage.setItem('github_pat', token);
            localStorage.setItem('github_user', JSON.stringify(user));
            
            // Success
            this.closeAuthModal();
            window.dispatchEvent(new Event('authSuccess'));
            this.showToast('Successfully authenticated!', 'success');
            
        } catch (error) {
            this.showError('Authentication failed. Please check your token.');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
    
    // Logout
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('github_pat');
        localStorage.removeItem('github_user');
        window.dispatchEvent(new Event('authLogout'));
        this.showToast('Logged out successfully', 'info');
    }
    
    // Close auth modal
    closeAuthModal() {
        document.querySelector('.auth-modal')?.remove();
    }
    
    // Show error
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'auth-error';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        
        const modal = document.querySelector('.auth-modal-content');
        const existing = modal.querySelector('.auth-error');
        if (existing) existing.remove();
        
        modal.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 3000);
    }
    
    // Show toast
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : 'info'}-circle"></i> ${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
}

// Initialize
window.githubAuth = new GitHubAuth();

// Update UI based on auth state
function updateAuthUI() {
    const nav = document.querySelector('.main-nav');
    const existingAuth = document.getElementById('authSection');
    if (existingAuth) existingAuth.remove();
    
    const authSection = document.createElement('div');
    authSection.id = 'authSection';
    authSection.className = 'auth-section';
    
    if (window.githubAuth.isAuthenticated()) {
        const user = window.githubAuth.getUser();
        authSection.innerHTML = `
            <div class="user-menu">
                <img src="${user.avatar_url}" alt="${user.login}" class="user-avatar">
                <span class="user-name">${user.name || user.login}</span>
                <button onclick="window.githubAuth.logout()" class="btn-text">Logout</button>
            </div>
        `;
    } else {
        authSection.innerHTML = `
            <button onclick="window.githubAuth.login()" class="btn-secondary">
                <i class="fab fa-github"></i> Login with GitHub
            </button>
        `;
    }
    
    nav.insertBefore(authSection, nav.lastElementChild);
}

// Listen for auth events
window.addEventListener('authSuccess', updateAuthUI);
window.addEventListener('authLogout', () => {
    updateAuthUI();
    location.reload(); // Refresh to update UI
});

// Update on load
document.addEventListener('DOMContentLoaded', updateAuthUI);