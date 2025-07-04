// GitHub OAuth Authentication Handler
class GitHubAuth {
    constructor() {
        // GitHub OAuth App settings (you'll need to create an OAuth App)
        this.clientId = 'YOUR_GITHUB_OAUTH_CLIENT_ID'; // Replace with actual client ID
        
        // Auto-detect redirect URI based on current location
        this.redirectUri = window.location.origin + window.location.pathname;
        this.scope = 'public_repo'; // Only need public repo access
        
        // Check for existing auth
        this.token = localStorage.getItem('github_oauth_token');
        this.user = JSON.parse(localStorage.getItem('github_user') || 'null');
        
        // Handle OAuth callback
        this.handleCallback();
    }
    
    // Check if user is authenticated
    isAuthenticated() {
        return !!this.token && !!this.user;
    }
    
    // Get current user
    getUser() {
        return this.user;
    }
    
    // Get auth token
    getToken() {
        return this.token;
    }
    
    // Initiate OAuth login flow
    login() {
        const authUrl = `https://github.com/login/oauth/authorize?` +
            `client_id=${this.clientId}&` +
            `redirect_uri=${encodeURIComponent(this.redirectUri)}&` +
            `scope=${encodeURIComponent(this.scope)}&` +
            `state=${this.generateState()}`;
        
        // Save current state for security
        sessionStorage.setItem('oauth_state', this.state);
        
        // Redirect to GitHub
        window.location.href = authUrl;
    }
    
    // Handle OAuth callback
    async handleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (code && state) {
            // Verify state to prevent CSRF
            const savedState = sessionStorage.getItem('oauth_state');
            if (state !== savedState) {
                console.error('OAuth state mismatch');
                return;
            }
            
            // Exchange code for token using a proxy service
            // Note: This requires a backend service to keep client_secret secure
            try {
                const token = await this.exchangeCodeForToken(code);
                if (token) {
                    this.token = token;
                    localStorage.setItem('github_oauth_token', token);
                    
                    // Get user info
                    await this.fetchUserInfo();
                    
                    // Clean up URL
                    window.history.replaceState({}, '', this.redirectUri);
                    
                    // Trigger auth success event
                    window.dispatchEvent(new Event('authSuccess'));
                }
            } catch (error) {
                console.error('OAuth error:', error);
                this.showAuthError();
            }
            
            // Clean up
            sessionStorage.removeItem('oauth_state');
        }
    }
    
    // Exchange authorization code for access token
    async exchangeCodeForToken(code) {
        // For GitHub Pages, we need a serverless function or proxy service
        // Options:
        // 1. Use Netlify Functions, Vercel Functions, or AWS Lambda
        // 2. Use a service like Auth0 or Firebase Auth
        // 3. Use GitHub's device flow (beta)
        
        // Example using a Netlify function:
        const response = await fetch('/.netlify/functions/github-auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code })
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.access_token;
        }
        
        // Fallback: For demo purposes, show instructions
        this.showAuthInstructions();
        return null;
    }
    
    // Fetch user information
    async fetchUserInfo() {
        if (!this.token) return;
        
        try {
            const response = await fetch('https://api.github.com/user', {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });
            
            if (response.ok) {
                this.user = await response.json();
                localStorage.setItem('github_user', JSON.stringify(this.user));
            }
        } catch (error) {
            console.error('Error fetching user info:', error);
        }
    }
    
    // Logout
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('github_oauth_token');
        localStorage.removeItem('github_user');
        window.dispatchEvent(new Event('authLogout'));
    }
    
    // Generate random state for OAuth
    generateState() {
        this.state = Math.random().toString(36).substring(2, 15) + 
                     Math.random().toString(36).substring(2, 15);
        return this.state;
    }
    
    // Show authentication instructions for demo
    showAuthInstructions() {
        const modal = document.createElement('div');
        modal.className = 'auth-modal';
        modal.innerHTML = `
            <div class="auth-modal-content">
                <h3>GitHub Authentication Setup</h3>
                <p>To enable GitHub authentication, you need to:</p>
                <ol>
                    <li>Create a GitHub OAuth App in your GitHub settings</li>
                    <li>Set the callback URL to: <code>${this.redirectUri}</code></li>
                    <li>Deploy a serverless function to handle the OAuth flow</li>
                </ol>
                <p>For testing, you can use a Personal Access Token:</p>
                <input type="password" id="patInput" placeholder="Enter your GitHub Personal Access Token">
                <button onclick="window.auth.usePersonalAccessToken()">Use Token</button>
                <button onclick="this.parentElement.parentElement.remove()">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Alternative: Use Personal Access Token for testing
    async usePersonalAccessToken() {
        const input = document.getElementById('patInput');
        const token = input.value.trim();
        
        if (token) {
            this.token = token;
            localStorage.setItem('github_oauth_token', token);
            
            // Fetch user info
            await this.fetchUserInfo();
            
            // Close modal
            document.querySelector('.auth-modal').remove();
            
            // Trigger auth success
            window.dispatchEvent(new Event('authSuccess'));
        }
    }
    
    // Show auth error
    showAuthError() {
        const toast = document.createElement('div');
        toast.className = 'toast error';
        toast.textContent = 'Authentication failed. Please try again.';
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
}

// Initialize auth
window.auth = new GitHubAuth();

// Add auth UI components
document.addEventListener('DOMContentLoaded', () => {
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
    
    if (window.auth.isAuthenticated()) {
        const user = window.auth.getUser();
        authSection.innerHTML = `
            <div class="user-menu">
                <img src="${user.avatar_url}" alt="${user.login}" class="user-avatar">
                <span class="user-name">${user.name || user.login}</span>
                <button onclick="window.auth.logout()" class="btn-text">Logout</button>
            </div>
        `;
    } else {
        authSection.innerHTML = `
            <button onclick="window.auth.login()" class="btn-secondary">
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
    location.reload(); // Refresh to clear any authenticated content
});