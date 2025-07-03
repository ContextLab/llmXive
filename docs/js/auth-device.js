// GitHub Device Flow Authentication
// This works better for static sites without a backend

class GitHubDeviceAuth {
    constructor() {
        this.clientId = '8ea31e8dfd8c6a0e4fe0'; // Replace with your OAuth App Client ID
        this.scope = 'public_repo';
        this.deviceCodeEndpoint = 'https://github.com/login/device/code';
        this.tokenEndpoint = 'https://github.com/login/oauth/access_token';
        
        // Check for existing auth
        this.token = localStorage.getItem('github_token');
        this.user = JSON.parse(localStorage.getItem('github_user') || 'null');
        
        // For production, you'd want to validate the token is still valid
        if (this.token) {
            this.validateToken();
        }
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
    
    // Start device flow authentication
    async login() {
        try {
            // Step 1: Request device code
            const deviceResponse = await fetch(this.deviceCodeEndpoint, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: this.clientId,
                    scope: this.scope
                })
            });
            
            if (!deviceResponse.ok) {
                throw new Error('Failed to get device code');
            }
            
            const deviceData = await deviceResponse.json();
            
            // Show user the verification UI
            this.showDeviceAuthModal(deviceData);
            
            // Step 2: Poll for token
            const token = await this.pollForToken(deviceData);
            
            if (token) {
                this.token = token;
                localStorage.setItem('github_token', token);
                
                // Get user info
                await this.fetchUserInfo();
                
                // Close modal and trigger success
                this.closeAuthModal();
                window.dispatchEvent(new Event('authSuccess'));
            }
            
        } catch (error) {
            console.error('Authentication error:', error);
            this.showError('Authentication failed. Please try again.');
        }
    }
    
    // Show device authentication modal
    showDeviceAuthModal(deviceData) {
        const modal = document.createElement('div');
        modal.id = 'deviceAuthModal';
        modal.className = 'auth-modal';
        modal.innerHTML = `
            <div class="auth-modal-content device-auth">
                <h3><i class="fab fa-github"></i> GitHub Authentication</h3>
                
                <div class="device-code-display">
                    <p>Enter this code on GitHub:</p>
                    <div class="code-box">
                        <span class="device-code">${deviceData.user_code}</span>
                        <button onclick="window.deviceAuth.copyCode('${deviceData.user_code}')" class="copy-btn">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </div>
                
                <div class="auth-steps">
                    <p>Steps to authenticate:</p>
                    <ol>
                        <li>Click the button below to open GitHub</li>
                        <li>Enter the code shown above</li>
                        <li>Authorize llmXive to access your account</li>
                        <li>Return here - authentication will complete automatically</li>
                    </ol>
                </div>
                
                <div class="auth-actions">
                    <button onclick="window.open('${deviceData.verification_uri}', '_blank')" class="btn-primary">
                        <i class="fas fa-external-link-alt"></i> Open GitHub
                    </button>
                    <button onclick="window.deviceAuth.cancelAuth()" class="btn-secondary">Cancel</button>
                </div>
                
                <div class="auth-status">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Waiting for authentication...</span>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Store for polling
        this.currentDeviceData = deviceData;
        this.authModal = modal;
    }
    
    // Poll for access token
    async pollForToken(deviceData) {
        const interval = deviceData.interval || 5;
        const expiresAt = Date.now() + (deviceData.expires_in * 1000);
        
        while (Date.now() < expiresAt) {
            await new Promise(resolve => setTimeout(resolve, interval * 1000));
            
            try {
                const response = await fetch(this.tokenEndpoint, {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        client_id: this.clientId,
                        device_code: deviceData.device_code,
                        grant_type: 'urn:ietf:params:oauth:grant-type:device_code'
                    })
                });
                
                const data = await response.json();
                
                if (data.access_token) {
                    return data.access_token;
                } else if (data.error === 'authorization_pending') {
                    // Continue polling
                    continue;
                } else if (data.error === 'slow_down') {
                    // Increase interval
                    await new Promise(resolve => setTimeout(resolve, 5000));
                } else {
                    throw new Error(data.error || 'Authentication failed');
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }
        
        throw new Error('Authentication timeout');
    }
    
    // Copy code to clipboard
    copyCode(code) {
        navigator.clipboard.writeText(code).then(() => {
            this.showToast('Code copied to clipboard!', 'success');
        });
    }
    
    // Cancel authentication
    cancelAuth() {
        this.closeAuthModal();
    }
    
    // Close auth modal
    closeAuthModal() {
        if (this.authModal) {
            this.authModal.remove();
            this.authModal = null;
        }
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
            } else if (response.status === 401) {
                // Token is invalid
                this.logout();
            }
        } catch (error) {
            console.error('Error fetching user info:', error);
        }
    }
    
    // Validate existing token
    async validateToken() {
        if (!this.token) return;
        
        try {
            const response = await fetch('https://api.github.com/user', {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });
            
            if (!response.ok) {
                this.logout();
            }
        } catch (error) {
            console.error('Token validation error:', error);
        }
    }
    
    // Logout
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('github_token');
        localStorage.removeItem('github_user');
        window.dispatchEvent(new Event('authLogout'));
    }
    
    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
    
    // Show error
    showError(message) {
        this.showToast(message, 'error');
    }
}

// Initialize device auth
window.deviceAuth = new GitHubDeviceAuth();

// Override the auth object to use device flow
window.auth = window.deviceAuth;

// Add device auth specific styles
const style = document.createElement('style');
style.textContent = `
.device-auth {
    max-width: 450px;
}

.device-code-display {
    text-align: center;
    margin: 2rem 0;
}

.code-box {
    display: inline-flex;
    align-items: center;
    gap: 1rem;
    background: var(--gray-100);
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    margin-top: 0.5rem;
}

.device-code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: var(--primary-color);
}

.copy-btn {
    background: white;
    border: 1px solid var(--gray-300);
    padding: 0.5rem;
    border-radius: 0.375rem;
    cursor: pointer;
    transition: var(--transition);
}

.copy-btn:hover {
    background: var(--gray-50);
    border-color: var(--gray-400);
}

.auth-steps {
    margin: 2rem 0;
}

.auth-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin: 2rem 0;
}

.auth-status {
    text-align: center;
    color: var(--gray-600);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}
`;
document.head.appendChild(style);