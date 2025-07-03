// Main application logic
(function() {
    'use strict';
    
    // Load projects on page load
    async function loadProjects() {
        try {
            // Show loading state
            ui.projectsGrid.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading projects...</p>
                </div>
            `;
            
            // Fetch projects
            const projects = await api.fetchProjectIssues();
            
            // Display projects
            ui.displayProjects(projects);
            
            // Load papers (if any)
            const papers = await api.fetchCompletedPapers();
            ui.displayPapers(papers);
            
        } catch (error) {
            console.error('Error loading projects:', error);
            ui.projectsGrid.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load projects</p>
                    <button onclick="loadProjects()" class="btn-secondary">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
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
            }
            
            // Focus search with Ctrl/Cmd + K
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                ui.searchInput.focus();
            }
        });
        
        // Add loading states to forms
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.classList.add('loading');
                }
            });
        });
        
        // Handle offline/online states
        window.addEventListener('offline', () => {
            ui.showToast('You are offline. Some features may not work.', 'warning');
        });
        
        window.addEventListener('online', () => {
            ui.showToast('Back online!', 'success');
            loadProjects();
        });
        
        // Performance optimization: Lazy load images
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img.lazy').forEach(img => {
                imageObserver.observe(img);
            });
        }
        
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
                ui.showToast('Refreshing...', 'info');
            }
        }, { passive: true });
        
        // Debug mode
        if (window.location.search.includes('debug=true')) {
            window.DEBUG = true;
            console.log('Debug mode enabled');
            console.log('Config:', CONFIG);
            console.log('Auth:', window.auth);
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
    
    // Analytics (optional)
    if (window.location.hostname === 'contextlab.github.io') {
        // Add analytics code here if needed
    }
    
})();