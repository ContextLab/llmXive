// Main application logic
(function() {
    'use strict';
    
    // Load projects on page load
    async function loadProjects() {
        try {
            await window.ui.loadProjects();
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }
    
    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', () => {
        // Load projects
        loadProjects();
        
        // Set up periodic refresh (every 5 minutes)
        setInterval(loadProjects, 5 * 60 * 1000);
        
        // Handle auth state changes
        window.addEventListener('authSuccess', () => {
            // Reload to show authenticated features
            loadProjects();
        });
        
        // Smooth scroll for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#' || targetId === '#submit') return;
                
                e.preventDefault();
                const target = document.querySelector(targetId);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Close modals with Escape
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.active').forEach(modal => {
                    modal.classList.remove('active');
                });
                document.querySelector('.auth-modal')?.remove();
            }
            
            // Focus search with Ctrl/Cmd + K
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                if (searchInput) searchInput.focus();
            }
        });
        
        // Handle offline/online states
        window.addEventListener('offline', () => {
            window.ui.showToast('You are offline. Some features may not work.', 'error');
        });
        
        window.addEventListener('online', () => {
            window.ui.showToast('Back online!', 'success');
            loadProjects();
        });
        
        // Add pull-to-refresh on mobile
        let touchStartY = 0;
        let touchEndY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            touchEndY = e.changedTouches[0].clientY;
            
            if (touchEndY - touchStartY > 100 && window.scrollY === 0) {
                loadProjects();
                window.ui.showToast('Refreshing...', 'info');
            }
        }, { passive: true });
        
        // Debug mode
        if (window.location.search.includes('debug=true')) {
            window.DEBUG = true;
            console.log('Debug mode enabled');
            console.log('Config:', CONFIG);
            console.log('Auth:', window.githubAuth);
            console.log('API:', window.api);
            console.log('UI:', window.ui);
        }
    });
    
    // Expose loadProjects globally
    window.loadProjects = loadProjects;
    
    // Service worker for offline support (optional)
    if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
        navigator.serviceWorker.register('/llmXive/sw.js').catch(err => {
            console.log('Service worker registration failed:', err);
        });
    }
    
})();