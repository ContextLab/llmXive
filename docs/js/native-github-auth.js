// Native GitHub Authentication - No tokens required
class NativeGitHubAuth {
    constructor() {
        // Check if user is logged into GitHub by testing API access
        this.checkGitHubSession();
    }
    
    // Check if user has active GitHub session
    async checkGitHubSession() {
        try {
            // GitHub allows basic read access to public repos without auth
            const response = await fetch('https://api.github.com/user', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const user = await response.json();
                this.user = user;
                localStorage.setItem('github_user', JSON.stringify(user));
            }
        } catch (error) {
            // User not logged in or CORS prevents checking
            this.user = null;
        }
    }
    
    // Show login instructions
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
                    <p class="auth-intro">To vote and create issues, you need to be logged into GitHub.</p>
                    
                    <div class="login-options">
                        <div class="login-option">
                            <h4>Already have a GitHub account?</h4>
                            <a href="https://github.com/login" target="_blank" class="btn-github">
                                <i class="fab fa-github"></i> Sign in to GitHub
                            </a>
                            <p class="helper-text">After signing in, return here and refresh the page</p>
                        </div>
                        
                        <div class="login-option">
                            <h4>New to GitHub?</h4>
                            <a href="https://github.com/signup" target="_blank" class="btn-secondary">
                                <i class="fas fa-user-plus"></i> Create an account
                            </a>
                            <p class="helper-text">It's free and takes just a minute</p>
                        </div>
                    </div>
                    
                    <div class="why-github">
                        <h4>Why GitHub?</h4>
                        <ul>
                            <li><i class="fas fa-check"></i> Vote on research ideas</li>
                            <li><i class="fas fa-check"></i> Submit your own ideas</li>
                            <li><i class="fas fa-check"></i> Track project progress</li>
                            <li><i class="fas fa-check"></i> Collaborate with researchers</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Simplified auth check
    isAuthenticated() {
        // For GitHub Pages, we can't truly check auth status
        // So we provide a "Continue with GitHub" flow
        return false;
    }
    
    // Direct GitHub actions
    voteOnIssue(issueNumber, reaction) {
        // Open GitHub issue page for voting
        const url = `https://github.com/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/${issueNumber}`;
        window.open(url, '_blank');
        this.showToast('Opening GitHub to vote. Click the 👍 or 👎 reaction on the issue.', 'info');
    }
    
    createIssue(title, body, labels) {
        // Use GitHub's issue creation URL
        const params = new URLSearchParams({
            title: title,
            body: body + '\n\n---\n*Submitted via llmXive Dashboard*',
            labels: labels.join(',')
        });
        
        const url = `https://github.com/${CONFIG.github.owner}/${CONFIG.github.repo}/issues/new?${params}`;
        window.open(url, '_blank');
        this.showToast('Opening GitHub to create your issue. Please submit it there.', 'info');
    }
    
    // Show toast notification
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
window.githubAuth = new NativeGitHubAuth();

// Simplified UI updates
function updateAuthUI() {
    const nav = document.querySelector('.main-nav');
    const existingAuth = document.getElementById('authSection');
    if (existingAuth) existingAuth.remove();
    
    const authSection = document.createElement('div');
    authSection.id = 'authSection';
    authSection.className = 'auth-section';
    
    authSection.innerHTML = `
        <a href="https://github.com/${CONFIG.github.owner}/${CONFIG.github.repo}" 
           target="_blank" 
           class="btn-github-nav">
            <i class="fab fa-github"></i> View on GitHub
        </a>
    `;
    
    nav.insertBefore(authSection, nav.lastElementChild);
}

// Update on load
document.addEventListener('DOMContentLoaded', updateAuthUI);