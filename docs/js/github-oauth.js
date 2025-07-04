// GitHub OAuth using Device Flow (suitable for static sites)
class GitHubOAuth {
    constructor() {
        this.clientId = 'Ov23li9dmD5V5g8Xpvw1'; // Public client ID for llmXive
        this.scope = 'public_repo';
        this.deviceCodeUrl = 'https://github.com/login/device/code';
        this.tokenUrl = 'https://github.com/login/oauth/access_token';
        
        this.token = localStorage.getItem('github_token');
        this.user = JSON.parse(localStorage.getItem('github_user') || 'null');
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
    
    // Login with GitHub button
    async login() {
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = `
            <div class="auth-modal-content">
                <button class="modal-close" onclick="window.githubAuth.closeAuthModal()">
                    <i class="fas fa-times"></i>
                </button>
                <div class="github-login">
                    <h3><i class="fab fa-github"></i> Login with GitHub</h3>
                    <p>Click below to authenticate with your GitHub account</p>
                    <button class="btn-github" onclick="window.githubAuth.startOAuthFlow()">
                        <i class="fab fa-github"></i> Login with GitHub
                    </button>
                    <div class="auth-note">
                        <i class="fas fa-lock"></i>
                        Secure authentication via GitHub OAuth
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Start OAuth flow
    async startOAuthFlow() {
        // For a truly static site, we'll use GitHub's OAuth web flow with a redirect
        const redirectUri = window.location.origin + window.location.pathname;
        const state = Math.random().toString(36).substring(7);
        localStorage.setItem('oauth_state', state);
        
        const authUrl = `https://github.com/login/oauth/authorize?` +
            `client_id=${this.clientId}&` +
            `redirect_uri=${encodeURIComponent(redirectUri)}&` +
            `scope=${this.scope}&` +
            `state=${state}`;
        
        window.location.href = authUrl;
    }
    
    // Handle OAuth callback
    async handleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (code && state === localStorage.getItem('oauth_state')) {
            // For static sites, we need to use a proxy service or ask users to create a PAT
            this.showTokenInstructions(code);
            
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
            localStorage.removeItem('oauth_state');
        }
    }
    
    // Show instructions for completing auth
    showTokenInstructions(code) {
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = `
            <div class="auth-modal-content">
                <button class="modal-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
                <h3><i class="fab fa-github"></i> Complete Authentication</h3>
                <div class="auth-instructions">
                    <p>To complete authentication, you have two options:</p>
                    
                    <div class="auth-option">
                        <h4>Option 1: Use the llmXive Auth Service</h4>
                        <p>Visit <a href="https://llmxive-auth.herokuapp.com/auth?code=${code}" target="_blank">our auth service</a> to complete authentication.</p>
                        <button class="btn-primary" onclick="window.open('https://llmxive-auth.herokuapp.com/auth?code=${code}', '_blank')">
                            <i class="fas fa-external-link-alt"></i> Complete Auth
                        </button>
                    </div>
                    
                    <div class="auth-option">
                        <h4>Option 2: Create a Personal Access Token</h4>
                        <p>For maximum security, create your own token:</p>
                        <ol>
                            <li>Go to <a href="https://github.com/settings/tokens/new" target="_blank">GitHub Token Settings</a></li>
                            <li>Name: "llmXive Dashboard"</li>
                            <li>Expiration: 90 days recommended</li>
                            <li>Scope: <code>public_repo</code></li>
                            <li>Click "Generate token" and paste below</li>
                        </ol>
                        <input type="password" id="patInput" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" class="pat-input">
                        <button onclick="window.githubAuth.authenticateWithToken()" class="btn-secondary">
                            <i class="fas fa-key"></i> Use Token
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Fallback to PAT authentication
    async authenticateWithToken() {
        const input = document.getElementById('patInput');
        const token = input.value.trim();
        
        if (!token) {
            this.showError('Please enter a token');
            return;
        }
        
        try {
            // Test token
            const response = await fetch('https://api.github.com/user', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Invalid token');
            }
            
            const user = await response.json();
            
            // Save
            this.token = token;
            this.user = user;
            localStorage.setItem('github_token', token);
            localStorage.setItem('github_user', JSON.stringify(user));
            
            // Success
            document.querySelector('.auth-modal')?.remove();
            window.dispatchEvent(new Event('authSuccess'));
            this.showToast('Successfully authenticated!', 'success');
            
        } catch (error) {
            this.showError('Authentication failed. Please check your token.');
        }
    }
    
    // Logout
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('github_token');
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

// Initialize and handle OAuth callback
window.githubAuth = new GitHubOAuth();

// Check for OAuth callback on page load
document.addEventListener('DOMContentLoaded', () => {
    window.githubAuth.handleCallback();
    updateAuthUI();
});

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
            <button onclick="window.githubAuth.login()" class="btn-github-small">
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
    location.reload();
});