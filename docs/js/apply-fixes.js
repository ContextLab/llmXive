// Main file to apply all fixes to the llmXive GitHub Pages site

(function() {
    'use strict';
    
    console.log('Applying llmXive UI fixes...');
    
    // Wait for all components to be loaded
    function waitForComponents() {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (window.githubAPI && window.ui && window.githubAuth) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
            
            // Timeout after 10 seconds
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve();
            }, 10000);
        });
    }
    
    // Apply all fixes
    async function applyAllFixes() {
        await waitForComponents();
        
        console.log('Components loaded, applying fixes...');
        
        // 1. Apply project board fix FIRST (most important)
        if (window.projectBoardFix) {
            console.log('Applying project board fix...');
            window.projectBoardFix.applyFix();
        }
        
        // 2. Apply voting system refactor (replaces old voting fixes)
        if (window.votingSystemRefactor && window.ui && window.githubAuth) {
            console.log('Applying voting system refactor...');
            window.votingSystemRefactor.applyFix();
        }
        
        // 3. Apply board UI fixes for author display
        if (window.boardUIFixes && window.ui) {
            console.log('Applying board UI fixes...');
            window.boardUIFixes.applyFixes(window.ui);
        }
        
        // Note: Removed old githubAPIFixes as it's replaced by projectBoardFix
        
        // 4. Override the main loadProjects function to include all enhancements
        if (window.ui) {
            const originalLoadProjects = window.ui.loadProjects.bind(window.ui);
            
            window.ui.loadProjects = async function() {
                console.log('Loading projects with enhancements...');
                
                try {
                    // First load issues normally
                    const issues = await window.githubAPI.fetchIssues();
                    
                    // Enhance with model authors
                    const enhancedIssues = await window.modelAuthorParser.enhanceIssuesWithModelAuthors(issues);
                    
                    // Store and render
                    this.projects = enhancedIssues;
                    this.filteredProjects = enhancedIssues;
                    this.renderProjects();
                    
                    // Update stats
                    this.updateStats();
                    
                } catch (error) {
                    console.error('Error loading projects:', error);
                    this.showToast('Failed to load projects. Please refresh.', 'error');
                }
            };
        }
        
        // 5. Add CSS fixes
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = 'css/modal-fixes.css';
        document.head.appendChild(cssLink);
        
        // 6. Trigger a reload of projects to apply all fixes
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects with fixes...');
            await window.ui.loadProjects();
        }
        
        console.log('All fixes applied successfully!');
    }
    
    // Apply fixes when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAllFixes);
    } else {
        applyAllFixes();
    }
    
    // Also apply fixes if components load later
    window.addEventListener('componentsLoaded', applyAllFixes);
    
})();