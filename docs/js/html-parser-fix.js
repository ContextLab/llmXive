// Fix that parses project board status directly from GitHub HTML
(function() {
    console.log('Applying HTML parser project board fix...');
    
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
    
    // Fetch issue page and parse project status
    async function getIssueProjectStatus(issueNumber) {
        try {
            const url = `https://github.com/ContextLab/llmXive/issues/${issueNumber}`;
            
            // Use a CORS proxy to fetch the HTML
            const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`;
            
            const response = await fetch(proxyUrl);
            if (!response.ok) {
                console.error(`Failed to fetch issue #${issueNumber}:`, response.status);
                return null;
            }
            
            const data = await response.json();
            const html = data.contents;
            
            // Parse the HTML to find project status
            // Look for the project board status in the sidebar
            const projectMatch = html.match(/data-board-column="([^"]+)"/);
            if (projectMatch) {
                const status = projectMatch[1];
                const normalized = statusNormalizationMap[status.toLowerCase()] || status;
                console.log(`Issue #${issueNumber}: Found status "${status}" -> "${normalized}"`);
                return normalized;
            }
            
            // Alternative: Look for project status in the issue metadata
            const metaMatch = html.match(/Project.*?Status.*?<span[^>]*>([^<]+)<\/span>/si);
            if (metaMatch) {
                const status = metaMatch[1].trim();
                const normalized = statusNormalizationMap[status.toLowerCase()] || status;
                console.log(`Issue #${issueNumber}: Found status "${status}" -> "${normalized}"`);
                return normalized;
            }
            
            console.log(`Issue #${issueNumber}: No project status found in HTML`);
            return null;
            
        } catch (error) {
            console.error(`Error fetching issue #${issueNumber}:`, error);
            return null;
        }
    }
    
    // Fetch project board page directly
    async function getProjectBoardStatuses() {
        try {
            console.log('Fetching project board HTML...');
            
            const url = 'https://github.com/orgs/ContextLab/projects/13';
            const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`;
            
            const response = await fetch(proxyUrl);
            if (!response.ok) {
                console.error('Failed to fetch project board:', response.status);
                return new Map();
            }
            
            const data = await response.json();
            const html = data.contents;
            
            const statusMap = new Map();
            
            // Parse project board HTML to find issues and their columns
            // Look for issue cards with their column information
            const cardMatches = html.matchAll(/data-issue-number="(\d+)".*?data-column="([^"]+)"/g);
            
            for (const match of cardMatches) {
                const issueNumber = parseInt(match[1]);
                const columnName = match[2];
                const normalized = statusNormalizationMap[columnName.toLowerCase()] || columnName;
                statusMap.set(issueNumber, normalized);
                
                if (issueNumber === 21) {
                    console.log(`Issue #21 found in column "${columnName}" -> "${normalized}"`);
                }
            }
            
            // Alternative parsing method
            if (statusMap.size === 0) {
                console.log('Trying alternative parsing method...');
                
                // Look for issue links within column containers
                const columnSections = html.split(/class="[^"]*project-column[^"]*"/);
                
                columnSections.forEach((section, index) => {
                    if (index === 0) return; // Skip content before first column
                    
                    // Extract column name
                    const columnMatch = section.match(/class="[^"]*column-header[^"]*"[^>]*>([^<]+)</);
                    if (columnMatch) {
                        const columnName = columnMatch[1].trim();
                        const normalized = statusNormalizationMap[columnName.toLowerCase()] || columnName;
                        
                        // Find all issue numbers in this column
                        const issueMatches = section.matchAll(/\/issues\/(\d+)/g);
                        for (const issueMatch of issueMatches) {
                            const issueNumber = parseInt(issueMatch[1]);
                            if (!statusMap.has(issueNumber)) {
                                statusMap.set(issueNumber, normalized);
                                
                                if (issueNumber === 21) {
                                    console.log(`Issue #21 found in column "${columnName}" -> "${normalized}"`);
                                }
                            }
                        }
                    }
                });
            }
            
            console.log(`Found ${statusMap.size} issues on project board`);
            return statusMap;
            
        } catch (error) {
            console.error('Error fetching project board:', error);
            
            // Fallback: fetch individual issue pages for a subset
            console.log('Falling back to individual issue fetching...');
            const statusMap = new Map();
            
            // Just check a few specific issues we know about
            const issuesToCheck = [21, 1, 5, 10, 22, 23, 24, 30];
            
            for (const issueNum of issuesToCheck) {
                const status = await getIssueProjectStatus(issueNum);
                if (status) {
                    statusMap.set(issueNum, status);
                }
            }
            
            return statusMap;
        }
    }
    
    async function applyFix() {
        if (fixApplied) return;
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding fetchProjectIssues with HTML parser...');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('Fetching issues with HTML-parsed project board status...');
            
            try {
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Get project board data by parsing HTML
                const projectStatuses = await getProjectBoardStatuses();
                
                if (projectStatuses.size === 0) {
                    console.error('No project board statuses found!');
                    return issues;
                }
                
                // Filter to only include issues on the project board
                const projectIssues = [];
                
                issues.forEach(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
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