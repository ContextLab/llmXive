// Proper fix to fetch project board status using REST API
(function() {
    console.log('Applying proper project board fix...');
    
    let fixApplied = false;
    
    // Status normalization map
    const statusNormalizationMap = {
        'backlog': 'Backlog',
        'ready': 'Ready',
        'in progress': 'In Progress',
        'in review': 'In Review',
        'done': 'Done'
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
    
    // Use REST API to get project data
    async function getProjectBoardStatuses() {
        console.log('Fetching project board data via REST API...');
        
        try {
            const headers = {
                'Accept': 'application/vnd.github+json'
            };
            
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
            }
            
            // First, get the project ID
            const projectsResponse = await fetch(
                'https://api.github.com/orgs/ContextLab/projects?per_page=100',
                { headers }
            );
            
            if (!projectsResponse.ok) {
                console.error('Failed to fetch projects:', projectsResponse.status);
                return new Map();
            }
            
            const projects = await projectsResponse.json();
            const llmXiveProject = projects.find(p => p.number === 13);
            
            if (!llmXiveProject) {
                console.error('Project #13 not found');
                return new Map();
            }
            
            console.log('Found project:', llmXiveProject.name);
            
            // Get project columns
            const columnsResponse = await fetch(
                `https://api.github.com/projects/${llmXiveProject.id}/columns`,
                { headers }
            );
            
            if (!columnsResponse.ok) {
                console.error('Failed to fetch columns:', columnsResponse.status);
                return new Map();
            }
            
            const columns = await columnsResponse.json();
            const statusMap = new Map();
            
            // For each column, get its cards
            for (const column of columns) {
                console.log(`Fetching cards for column: ${column.name}`);
                
                const cardsResponse = await fetch(
                    `https://api.github.com/projects/columns/${column.id}/cards?per_page=100`,
                    { headers }
                );
                
                if (!cardsResponse.ok) {
                    console.error(`Failed to fetch cards for column ${column.name}:`, cardsResponse.status);
                    continue;
                }
                
                const cards = await cardsResponse.json();
                
                // Extract issue numbers from content URLs
                for (const card of cards) {
                    if (card.content_url && card.content_url.includes('/issues/')) {
                        const issueNumber = parseInt(card.content_url.split('/').pop());
                        if (issueNumber) {
                            const normalizedStatus = statusNormalizationMap[column.name.toLowerCase()] || column.name;
                            statusMap.set(issueNumber, normalizedStatus);
                            
                            if (issueNumber === 21) {
                                console.log(`Issue #21 found in column "${column.name}" -> "${normalizedStatus}"`);
                            }
                        }
                    }
                }
            }
            
            console.log('Project board status map:', Array.from(statusMap.entries()));
            return statusMap;
            
        } catch (error) {
            console.error('Error fetching project board data:', error);
            return new Map();
        }
    }
    
    async function applyFix() {
        if (fixApplied) return;
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding fetchProjectIssues with proper project board integration...');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('Fetching issues with project board status...');
            
            try {
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Get project board data
                const projectStatuses = await getProjectBoardStatuses();
                
                if (projectStatuses.size === 0) {
                    console.warn('No project board data fetched, using label-based status');
                    return issues;
                }
                
                // Apply statuses and filter
                const issuesWithStatus = [];
                
                issues.forEach(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
                    if (projectStatus) {
                        // Issue is on project board
                        issuesWithStatus.push({
                            ...issue,
                            projectStatus: projectStatus
                        });
                        console.log(`Issue #${issue.number}: On project board with status "${projectStatus}"`);
                    } else {
                        // Issue not on project board - skip it
                        console.log(`Issue #${issue.number}: Not on project board, skipping`);
                    }
                });
                
                console.log(`Returning ${issuesWithStatus.length} issues that are on the project board`);
                return issuesWithStatus;
                
            } catch (error) {
                console.error('Error in fetchProjectIssues override:', error);
                return originalFetch();
            }
        };
        
        fixApplied = true;
        
        // Reload projects
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects with proper fix...');
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