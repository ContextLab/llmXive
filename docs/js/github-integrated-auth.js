// GitHub Integrated Authentication
// Uses GitHub's OAuth flow with a public proxy service for token exchange
class GitHubIntegratedAuth {
    constructor() {
        this.clientId = 'Ov23liY5hzeo5JVmlzcH';
        this.redirectUri = 'https://contextlab.github.io/llmXive/';
        
        // For token exchange, we'll use a public proxy or implement device flow
        this.useDeviceFlow = true; // Safer for static sites
        
        this.token = localStorage.getItem('github_token');
        this.user = JSON.parse(localStorage.getItem('github_user') || 'null');
        
        // Check for OAuth callback
        this.handleCallback();
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
    
    // Show login options
    async login() {
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = `
            <div class="auth-modal-content light-modal">
                <button class="modal-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
                <div class="github-login">
                    <h3><i class="fab fa-github"></i> Login with GitHub</h3>
                    <p class="auth-intro">Choose how you'd like to authenticate:</p>
                    
                    <div class="auth-options">
                        <div class="auth-option primary">
                            <h4><i class="fas fa-mobile-alt"></i> Device Flow (Recommended)</h4>
                            <p>Get a code and enter it on GitHub - works everywhere!</p>
                            <button onclick="window.githubAuth.startDeviceFlow()" class="btn-github">
                                <i class="fas fa-mobile-alt"></i> Use Device Flow
                            </button>
                        </div>
                        
                        <div class="auth-option">
                            <h4><i class="fas fa-key"></i> Personal Access Token</h4>
                            <p>Create your own token for maximum control</p>
                            <button onclick="window.githubAuth.showTokenAuth()" class="btn-secondary">
                                <i class="fas fa-key"></i> Use Token
                            </button>
                        </div>
                        
                        <div class="auth-option">
                            <h4><i class="fab fa-github"></i> OAuth Flow</h4>
                            <p>Standard GitHub login (requires backend)</p>
                            <button onclick="window.githubAuth.startOAuthFlow()" class="btn-secondary">
                                <i class="fab fa-github"></i> Use OAuth
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Start Device Flow
    async startDeviceFlow() {
        try {
            // Request device code
            const response = await fetch('https://github.com/login/device/code', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: this.clientId,
                    scope: 'public_repo'
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start device flow');
            }
            
            const data = await response.json();
            this.showDeviceCode(data);
            this.pollForToken(data.device_code, data.interval || 5);
            
        } catch (error) {
            console.error('Device flow error:', error);
            this.showTokenAuth(); // Fallback to token auth
        }
    }
    
    // Show device code to user
    showDeviceCode(data) {
        const modal = document.querySelector('.auth-modal-content');
        modal.innerHTML = `
            <button class="modal-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
            <div class="device-flow">
                <h3><i class="fas fa-mobile-alt"></i> Device Authorization</h3>
                
                <div class="device-code-display">
                    <p>Enter this code on GitHub:</p>
                    <div class="code-box">${data.user_code}</div>
                </div>
                
                <a href="${data.verification_uri}" target="_blank" class="btn-github">
                    <i class="fas fa-external-link-alt"></i> Open GitHub
                </a>
                
                <div class="device-steps">
                    <ol>
                        <li>Click the button above or go to <code>${data.verification_uri}</code></li>
                        <li>Enter the code: <strong>${data.user_code}</strong></li>
                        <li>Authorize llmXive</li>
                        <li>Return here - we'll detect when you're done!</li>
                    </ol>
                </div>
                
                <div class="device-waiting">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Waiting for authorization...</p>
                </div>
            </div>
        `;
    }
    
    // Poll for token
    async pollForToken(deviceCode, interval) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch('https://github.com/login/oauth/access_token', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: this.clientId,
                        device_code: deviceCode,
                        grant_type: 'urn:ietf:params:oauth:grant-type:device_code'
                    })
                });
                
                const data = await response.json();
                
                if (data.access_token) {
                    clearInterval(pollInterval);
                    this.handleTokenReceived(data.access_token);
                } else if (data.error === 'authorization_pending') {
                    // Keep polling
                } else if (data.error === 'slow_down') {
                    // Increase interval
                    clearInterval(pollInterval);
                    this.pollForToken(deviceCode, interval + 5);
                } else {
                    // Error occurred
                    clearInterval(pollInterval);
                    this.showError('Authorization failed. Please try again.');
                }
            } catch (error) {
                clearInterval(pollInterval);
                this.showError('Network error. Please try again.');
            }
        }, interval * 1000);
    }
    
    // Show token auth
    showTokenAuth() {
        const modal = document.querySelector('.auth-modal-content') || this.createModal();
        modal.innerHTML = `
            <button class="modal-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
            <div class="token-auth">
                <h3><i class="fas fa-key"></i> Personal Access Token</h3>
                
                <div class="token-steps">
                    <p>Create a GitHub token with the following steps:</p>
                    <ol>
                        <li>
                            <a href="https://github.com/settings/tokens/new?description=llmXive%20Dashboard&scopes=public_repo" 
                               target="_blank" class="link-primary">
                                <i class="fas fa-external-link-alt"></i> Create Token
                            </a>
                        </li>
                        <li>Name: "llmXive Dashboard"</li>
                        <li>Expiration: 90 days recommended</li>
                        <li>Scope: <code>public_repo</code> (pre-selected)</li>
                        <li>Click "Generate token"</li>
                        <li>Copy and paste it below:</li>
                    </ol>
                </div>
                
                <div class="token-input-group">
                    <input type="password" 
                           id="tokenInput" 
                           placeholder="ghp_..." 
                           class="token-input">
                    <button onclick="window.githubAuth.authenticateWithToken()" 
                            class="btn-primary">
                        <i class="fas fa-sign-in-alt"></i> Authenticate
                    </button>
                </div>
                
                <div class="security-note">
                    <i class="fas fa-lock"></i>
                    Your token is stored locally and only sent to GitHub.
                </div>
            </div>
        `;
        
        setTimeout(() => {
            const input = document.getElementById('tokenInput');
            if (input) {
                input.focus();
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') this.authenticateWithToken();
                });
            }
        }, 100);
    }
    
    // Start OAuth flow (requires backend)
    startOAuthFlow() {
        const state = Math.random().toString(36).substring(7);
        localStorage.setItem('oauth_state', state);
        
        const params = new URLSearchParams({
            client_id: this.clientId,
            redirect_uri: this.redirectUri,
            scope: 'public_repo',
            state: state
        });
        
        window.location.href = `https://github.com/login/oauth/authorize?${params}`;
    }
    
    // Handle OAuth callback
    async handleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (code && state === localStorage.getItem('oauth_state')) {
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
            localStorage.removeItem('oauth_state');
            
            // Try to exchange code for token
            await this.exchangeCodeForToken(code);
        }
    }
    
    // Exchange authorization code for access token
    async exchangeCodeForToken(code) {
        // Show loading state
        const modal = this.createModal();
        modal.innerHTML = `
            <div class="oauth-loading">
                <h3><i class="fas fa-spinner fa-spin"></i> Completing Login...</h3>
                <p>Please wait while we authenticate you.</p>
            </div>
        `;
        
        try {
            // Try common proxy services first
            const proxyUrls = [
                // Add your deployed service URL here:
                // 'https://your-app.herokuapp.com/authenticate/',
                // 'https://your-netlify-site.netlify.app/.netlify/functions/github-auth?code=',
                
                // Fallback - show instructions
                null
            ];
            
            let token = null;
            
            for (const proxyUrl of proxyUrls) {
                if (!proxyUrl) break;
                
                try {
                    const response = await fetch(proxyUrl + code);
                    const data = await response.json();
                    
                    if (data.token || data.access_token) {
                        token = data.token || data.access_token;
                        break;
                    }
                } catch (e) {
                    console.log('Proxy failed:', proxyUrl);
                }
            }
            
            if (token) {
                await this.handleTokenReceived(token);
            } else {
                // No working proxy found, show setup instructions
                this.showBackendRequired(code);
            }
            
        } catch (error) {
            console.error('OAuth exchange error:', error);
            this.showBackendRequired(code);
        }
    }
    
    // Show backend required message
    showBackendRequired(code) {
        const modal = this.createModal();
        modal.innerHTML = `
            <button class="modal-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
            <div class="backend-required">
                <h3><i class="fas fa-server"></i> One More Step!</h3>
                <p>To complete OAuth setup, you need to deploy a simple auth proxy.</p>
                
                <div class="setup-options">
                    <div class="setup-option">
                        <h4>Option 1: Quick Setup with Gatekeeper (5 min)</h4>
                        <ol>
                            <li>
                                <a href="https://heroku.com/deploy?template=https://github.com/prose/gatekeeper" 
                                   target="_blank" class="btn-primary">
                                    <i class="fas fa-rocket"></i> Deploy to Heroku
                                </a>
                            </li>
                            <li>Use these settings:
                                <ul>
                                    <li>OAUTH_CLIENT_ID: <code>Ov23liY5hzeo5JVmlzcH</code></li>
                                    <li>OAUTH_CLIENT_SECRET: <em>Your secret from GitHub</em></li>
                                    <li>REDIRECT_URI: <code>https://contextlab.github.io/llmXive/</code></li>
                                </ul>
                            </li>
                            <li>Update the proxy URL in <code>github-integrated-auth.js</code></li>
                        </ol>
                    </div>
                    
                    <div class="setup-option">
                        <h4>Option 2: Read the Setup Guide</h4>
                        <a href="OAUTH_SETUP_GUIDE.md" target="_blank" class="btn-secondary">
                            <i class="fas fa-book"></i> View Setup Guide
                        </a>
                    </div>
                </div>
                
                <div class="divider">OR</div>
                
                <p>Use an alternative authentication method:</p>
                <div class="auth-alternatives">
                    <button onclick="window.githubAuth.showTokenAuth()" class="btn-secondary">
                        <i class="fas fa-key"></i> Personal Access Token
                    </button>
                    <button onclick="window.githubAuth.startDeviceFlow()" class="btn-secondary">
                        <i class="fas fa-mobile-alt"></i> Device Flow
                    </button>
                </div>
                
                <details class="debug-info">
                    <summary>Debug Info</summary>
                    <p>Authorization code: <code>${code}</code></p>
                    <p>This code expires in 10 minutes.</p>
                </details>
            </div>
        `;
    }
    
    // Authenticate with token
    async authenticateWithToken() {
        const input = document.getElementById('tokenInput');
        const token = input.value.trim();
        
        if (!token) {
            this.showError('Please enter a token');
            return;
        }
        
        try {
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
            this.handleTokenReceived(token, user);
            
        } catch (error) {
            this.showError('Invalid token. Please check and try again.');
        }
    }
    
    // Handle token received
    async handleTokenReceived(token, user = null) {
        this.token = token;
        localStorage.setItem('github_token', token);
        
        if (!user) {
            // Fetch user info
            const response = await fetch('https://api.github.com/user', {
                headers: this.getAuthHeaders()
            });
            user = await response.json();
        }
        
        this.user = user;
        localStorage.setItem('github_user', JSON.stringify(user));
        
        // Close modal and update UI
        document.querySelector('.auth-modal')?.remove();
        window.dispatchEvent(new Event('authSuccess'));
        this.showToast(`Welcome, ${user.name || user.login}!`, 'success');
    }
    
    // Create modal helper
    createModal() {
        const existingModal = document.querySelector('.auth-modal');
        if (existingModal) existingModal.remove();
        
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = '<div class="auth-modal-content light-modal"></div>';
        document.body.appendChild(modal);
        return modal.querySelector('.auth-modal-content');
    }
    
    // Vote on issue
    async vote(issueNumber, reaction) {
        if (!this.isAuthenticated()) {
            this.login();
            return false;
        }
        
        try {
            const response = await fetch(
                `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}/reactions`,
                {
                    method: 'POST',
                    headers: {
                        ...this.getAuthHeaders(),
                        'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                    },
                    body: JSON.stringify({ content: reaction })
                }
            );
            
            if (response.ok) {
                this.showToast('Vote recorded!', 'success');
                return true;
            } else if (response.status === 401) {
                this.logout();
                this.login();
                return false;
            }
        } catch (error) {
            console.error('Vote error:', error);
            // Fallback to GitHub redirect
            window.open(`https://github.com/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}`, '_blank');
            this.showToast('Please vote on the GitHub issue page', 'info');
            return false;
        }
    }
    
    // Create issue
    async createIssue(title, body, labels) {
        if (!this.isAuthenticated()) {
            this.login();
            return null;
        }
        
        try {
            const response = await fetch(
                `https://api.github.com/repos/${CONFIG.github.owner}/${CONFIG.github.repo}/issues`,
                {
                    method: 'POST',
                    headers: this.getAuthHeaders(),
                    body: JSON.stringify({
                        title,
                        body: body + '\n\n---\n*Submitted via llmXive Dashboard*',
                        labels
                    })
                }
            );
            
            if (response.ok) {
                const issue = await response.json();
                this.showToast('Issue created successfully!', 'success');
                return issue;
            } else if (response.status === 401) {
                this.logout();
                this.login();
                return null;
            }
        } catch (error) {
            console.error('Create issue error:', error);
            // Fallback to GitHub
            const params = new URLSearchParams({
                title: title,
                body: body + '\n\n---\n*Submitted via llmXive Dashboard*',
                labels: labels.join(',')
            });
            window.open(`https://github.com/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/new?${params}`, '_blank');
            return null;
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
    
    // Show error
    showError(message) {
        const container = document.querySelector('.auth-modal-content');
        if (!container) return;
        
        const existing = container.querySelector('.auth-error');
        if (existing) existing.remove();
        
        const error = document.createElement('div');
        error.className = 'auth-error';
        error.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        container.appendChild(error);
        
        setTimeout(() => error.remove(), 5000);
    }
    
    // Show toast
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';
        toast.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
}

// Initialize
window.githubAuth = new GitHubIntegratedAuth();

// Update UI
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
                <button onclick="window.githubAuth.logout()" class="btn-text">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </div>
        `;
    } else {
        authSection.innerHTML = `
            <button onclick="window.githubAuth.login()" class="btn-github-nav">
                <i class="fab fa-github"></i> Login with GitHub
            </button>
        `;
    }
    
    nav.insertBefore(authSection, nav.lastElementChild);
}

// Events
window.addEventListener('authSuccess', updateAuthUI);
window.addEventListener('authLogout', () => {
    updateAuthUI();
    location.reload();
});

document.addEventListener('DOMContentLoaded', updateAuthUI);