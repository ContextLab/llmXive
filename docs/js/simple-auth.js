// Simplified GitHub Integration - No complex OAuth needed!
class SimpleGitHubAuth {
    constructor() {
        this.owner = 'ContextLab';
        this.repo = 'llmXive';
        this.baseUrl = 'https://github.com';
        this.apiUrl = 'https://api.github.com';
        
        // Check if user is logged into GitHub by checking if they have a username stored
        this.username = localStorage.getItem('github_username');
    }
    
    // Check if user has identified themselves
    isIdentified() {
        return !!this.username;
    }
    
    // Get username
    getUsername() {
        return this.username;
    }
    
    // Simple "login" - just ask for their GitHub username
    async login() {
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = `
            <div class="auth-modal-content">
                <h3><i class="fab fa-github"></i> Connect with GitHub</h3>
                <p>Enter your GitHub username to personalize your experience:</p>
                <input type="text" id="githubUsername" placeholder="Your GitHub username" class="username-input">
                <div class="auth-actions">
                    <button onclick="window.simpleAuth.saveUsername()" class="btn-primary">
                        <i class="fas fa-check"></i> Continue
                    </button>
                    <button onclick="window.simpleAuth.skip()" class="btn-secondary">
                        Skip for now
                    </button>
                </div>
                <p class="auth-note">
                    <i class="fas fa-info-circle"></i> 
                    This is just for display purposes. You'll log in through GitHub when creating issues or voting.
                </p>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Focus input
        setTimeout(() => {
            document.getElementById('githubUsername').focus();
        }, 100);
        
        // Handle enter key
        document.getElementById('githubUsername').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.saveUsername();
            }
        });
    }
    
    // Save username
    saveUsername() {
        const input = document.getElementById('githubUsername');
        const username = input.value.trim();
        
        if (username) {
            this.username = username;
            localStorage.setItem('github_username', username);
            this.closeModal();
            window.dispatchEvent(new Event('authSuccess'));
        }
    }
    
    // Skip login
    skip() {
        this.closeModal();
    }
    
    // Close modal
    closeModal() {
        const modal = document.querySelector('.auth-modal');
        if (modal) {
            modal.remove();
        }
    }
    
    // Logout (just clear username)
    logout() {
        this.username = null;
        localStorage.removeItem('github_username');
        window.dispatchEvent(new Event('authLogout'));
    }
    
    // Create issue - redirect to GitHub
    createIssue(title, body, keywords = []) {
        // Add metadata to body
        const enhancedBody = `${body}

---
**Keywords**: ${keywords.join(', ') || 'none'}
**Submitted via**: [llmXive Dashboard](https://contextlab.github.io/llmXive/)
**Author**: @${this.username || 'anonymous'}`;
        
        // Create GitHub issue URL with pre-filled content
        const params = new URLSearchParams({
            title: title,
            body: enhancedBody,
            labels: keywords.join(',')
        });
        
        const issueUrl = `${this.baseUrl}/${this.owner}/${this.repo}/issues/new?${params}`;
        
        // Open in new tab
        window.open(issueUrl, '_blank');
        
        // Show success message
        this.showToast('Redirecting to GitHub to create your issue...', 'info');
    }
    
    // Vote on issue - redirect to GitHub
    voteOnIssue(issueNumber, voteType) {
        const issueUrl = `${this.baseUrl}/${this.owner}/${this.repo}/issues/${issueNumber}`;
        
        // Show instruction
        this.showVoteInstruction(voteType, issueUrl);
    }
    
    // Show vote instruction modal
    showVoteInstruction(voteType, issueUrl) {
        const emoji = voteType === 'up' ? '👍' : '👎';
        const modal = document.createElement('div');
        modal.className = 'auth-modal active';
        modal.innerHTML = `
            <div class="auth-modal-content vote-instruction">
                <h3>Vote on GitHub</h3>
                <p>To ${voteType === 'up' ? 'upvote' : 'downvote'} this issue:</p>
                <ol>
                    <li>Click the button below to open the issue on GitHub</li>
                    <li>Sign in to GitHub if prompted</li>
                    <li>Click the <strong>${emoji}</strong> reaction button</li>
                </ol>
                <div class="auth-actions">
                    <a href="${issueUrl}" target="_blank" class="btn-primary" onclick="window.simpleAuth.closeModal()">
                        <i class="fab fa-github"></i> Open on GitHub
                    </a>
                    <button onclick="window.simpleAuth.closeModal()" class="btn-secondary">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
}

// Initialize simple auth
window.simpleAuth = new SimpleGitHubAuth();

// Override the complex auth with simple auth
window.auth = window.simpleAuth;

// Update auth UI for simple approach
function updateAuthUI() {
    const nav = document.querySelector('.main-nav');
    const existingAuth = document.getElementById('authSection');
    if (existingAuth) existingAuth.remove();
    
    const authSection = document.createElement('div');
    authSection.id = 'authSection';
    authSection.className = 'auth-section';
    
    if (window.simpleAuth.isIdentified()) {
        const username = window.simpleAuth.getUsername();
        authSection.innerHTML = `
            <div class="user-menu">
                <i class="fab fa-github"></i>
                <span class="user-name">@${username}</span>
                <button onclick="window.simpleAuth.logout()" class="btn-text">Change</button>
            </div>
        `;
    } else {
        authSection.innerHTML = `
            <button onclick="window.simpleAuth.login()" class="btn-secondary">
                <i class="fab fa-github"></i> Connect GitHub
            </button>
        `;
    }
    
    nav.insertBefore(authSection, nav.lastElementChild);
}

// Listen for auth events
window.addEventListener('authSuccess', updateAuthUI);
window.addEventListener('authLogout', () => {
    updateAuthUI();
});

// Update on load
document.addEventListener('DOMContentLoaded', updateAuthUI);