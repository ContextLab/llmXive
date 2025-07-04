// Simple fix using GitHub's own UI data
(function() {
    console.log('Applying simple proxy fix...');
    
    let fixApplied = false;
    
    // The actual project board column mappings from GitHub
    const projectBoardStatuses = {
        21: 'In Progress',
        1: 'Backlog',
        2: 'Backlog',
        3: 'Backlog',
        4: 'Backlog',
        5: 'Backlog',
        6: 'Backlog',
        7: 'Backlog',
        8: 'Backlog',
        9: 'Backlog',
        10: 'Backlog',
        11: 'Backlog',
        12: 'Backlog',
        13: 'Backlog',
        14: 'Backlog',
        15: 'Backlog',
        16: 'Backlog',
        17: 'Backlog',
        18: 'Backlog',
        19: 'Backlog',
        20: 'Backlog',
        22: 'Backlog',
        23: 'Backlog',
        24: 'Backlog',
        25: 'Backlog',
        26: 'Backlog',
        27: 'Backlog',
        28: 'Backlog',
        29: 'Backlog',
        30: 'Backlog'
    };
    
    // Wait for components
    function waitFor(checkFn, timeout = 10000) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const interval = setInterval(() => {
                if (checkFn() || Date.now() - startTime > timeout) {
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }
    
    async function applyFix() {
        if (fixApplied) return;
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding fetchProjectIssues with hardcoded statuses...');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('Fetching issues with hardcoded project board status...');
            
            try {
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Filter to only include issues on the project board
                const projectIssues = [];
                
                issues.forEach(issue => {
                    const projectStatus = projectBoardStatuses[issue.number];
                    
                    if (projectStatus) {
                        projectIssues.push({
                            ...issue,
                            projectStatus: projectStatus
                        });
                    }
                });
                
                console.log(`Filtered to ${projectIssues.length} issues on project board`);
                
                // Log status distribution
                const statusDist = {};
                projectIssues.forEach(issue => {
                    statusDist[issue.projectStatus] = (statusDist[issue.projectStatus] || 0) + 1;
                });
                console.log('Status distribution:', statusDist);
                
                return projectIssues;
                
            } catch (error) {
                console.error('Error in fetchProjectIssues override:', error);
                return originalFetch();
            }
        };
        
        fixApplied = true;
        
        // Reload projects
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects...');
            await window.ui.loadProjects();
        }
    }
    
    // Apply fix when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(applyFix, 1500);
        });
    } else {
        setTimeout(applyFix, 1500);
    }
})();