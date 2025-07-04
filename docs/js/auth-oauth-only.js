// Fix to make login button use OAuth directly without showing options

(function() {
    'use strict';
    
    // Wait for githubAuth to be available
    function waitForAuth() {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (window.githubAuth) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
            
            // Timeout after 5 seconds
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve();
            }, 5000);
        });
    }
    
    async function applyOAuthOnlyFix() {
        await waitForAuth();
        
        if (!window.githubAuth) {
            console.warn('GitHub auth not found, cannot apply OAuth-only fix');
            return;
        }
        
        console.log('Applying OAuth-only login fix...');
        
        // Override the login method to go directly to OAuth
        window.githubAuth.login = function() {
            console.log('Redirecting to OAuth login...');
            this.startOAuthFlow();
        };
        
        // Also override the startOAuthFlow to show a nicer loading state
        const originalStartOAuth = window.githubAuth.startOAuthFlow.bind(window.githubAuth);
        
        window.githubAuth.startOAuthFlow = function() {
            // Show a loading modal while redirecting
            const existingModal = document.querySelector('.auth-modal');
            if (existingModal) existingModal.remove();
            
            const modal = document.createElement('div');
            modal.className = 'auth-modal active';
            modal.innerHTML = `
                <div class="auth-modal-content light-modal">
                    <div class="oauth-loading" style="text-align: center; padding: 2rem;">
                        <h3><i class="fab fa-github"></i> Redirecting to GitHub...</h3>
                        <div style="margin: 2rem 0;">
                            <i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: var(--primary-color);"></i>
                        </div>
                        <p>You'll be redirected to GitHub to authorize llmXive.</p>
                        <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                            Please wait...
                        </p>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Add a small delay for better UX
            setTimeout(() => {
                originalStartOAuth();
            }, 500);
        };
        
        console.log('OAuth-only login fix applied!');
    }
    
    // Apply fix when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyOAuthOnlyFix);
    } else {
        applyOAuthOnlyFix();
    }
    
})();