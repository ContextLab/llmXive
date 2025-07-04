// Parse project board status directly from GitHub HTML
(function() {
    console.log('Applying GitHub HTML parser fix...');
    
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
    
    // Fetch and parse the project board HTML
    async function fetchProjectBoardStatuses() {
        console.log('Fetching project board HTML...');
        
        try {
            // Use a CORS proxy to fetch the GitHub project board
            const projectUrl = 'https://github.com/orgs/ContextLab/projects/13/views/1';
            const proxyUrl = `https://corsproxy.io/?${encodeURIComponent(projectUrl)}`;
            
            console.log('Fetching via CORS proxy...');
            const response = await fetch(proxyUrl);
            
            if (!response.ok) {
                console.error('Failed to fetch project board:', response.status);
                // Try alternative proxy
                const altProxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(projectUrl)}`;
                console.log('Trying alternative proxy...');
                const altResponse = await fetch(altProxyUrl);
                if (!altResponse.ok) {
                    throw new Error('Both proxies failed');
                }
                const html = await altResponse.text();
                return parseProjectBoardHTML(html);
            }
            
            const html = await response.text();
            return parseProjectBoardHTML(html);
            
        } catch (error) {
            console.error('Error fetching project board:', error);
            
            // Fallback: Try fetching individual issue pages
            console.log('Falling back to issue page parsing...');
            return await fetchIssueStatuses();
        }
    }
    
    // Parse the project board HTML
    function parseProjectBoardHTML(html) {
        console.log('Parsing project board HTML...');
        const statusMap = new Map();
        
        try {
            // Method 1: Look for data attributes
            const issueMatches = html.matchAll(/data-card-issue-id="(\d+)"[^>]*data-column-name="([^"]+)"/g);
            for (const match of issueMatches) {
                const issueNumber = parseInt(match[1]);
                const columnName = match[2];
                const normalized = statusNormalizationMap[columnName.toLowerCase()] || columnName;
                statusMap.set(issueNumber, normalized);
            }
            
            // Method 2: Parse board structure
            if (statusMap.size === 0) {
                console.log('Trying alternative parsing method...');
                
                // Split by column containers
                const columnPattern = /<div[^>]*class="[^"]*column[^"]*"[^>]*>([\s\S]*?)<\/div>/g;
                const columns = html.match(columnPattern) || [];
                
                columns.forEach(columnHtml => {
                    // Extract column name
                    const nameMatch = columnHtml.match(/aria-label="([^"]+)"|data-column-name="([^"]+)"|<h[^>]*>([^<]+)<\/h/);
                    if (nameMatch) {
                        const columnName = (nameMatch[1] || nameMatch[2] || nameMatch[3]).trim();
                        const normalized = statusNormalizationMap[columnName.toLowerCase()] || columnName;
                        
                        // Find all issue numbers in this column
                        const issueMatches = columnHtml.matchAll(/\/issues\/(\d+)/g);
                        for (const issueMatch of issueMatches) {
                            const issueNumber = parseInt(issueMatch[1]);
                            if (!statusMap.has(issueNumber)) {
                                statusMap.set(issueNumber, normalized);
                            }
                        }
                    }
                });
            }
            
            // Method 3: Look for issue cards with project metadata
            if (statusMap.size === 0) {
                console.log('Trying issue card parsing...');
                
                const cardMatches = html.matchAll(/<article[^>]*>[\s\S]*?\/issues\/(\d+)[\s\S]*?<\/article>/g);
                for (const cardMatch of cardMatches) {
                    const issueNumber = parseInt(cardMatch[1]);
                    const cardHtml = cardMatch[0];
                    
                    // Look for status in the card
                    const statusMatch = cardHtml.match(/Status[:\s]*([^<\n]+)/i);
                    if (statusMatch) {
                        const status = statusMatch[1].trim();
                        const normalized = statusNormalizationMap[status.toLowerCase()] || status;
                        statusMap.set(issueNumber, normalized);
                    }
                }
            }
            
        } catch (error) {
            console.error('Error parsing HTML:', error);
        }
        
        console.log(`Parsed ${statusMap.size} issue statuses from project board`);
        return statusMap;
    }
    
    // Fallback: Fetch individual issue pages
    async function fetchIssueStatuses() {
        const statusMap = new Map();
        
        // For now, just check a few key issues
        const issuesToCheck = [21, 1, 5, 10, 22, 23, 24, 30];
        
        for (const issueNum of issuesToCheck) {
            try {
                const issueUrl = `https://github.com/ContextLab/llmXive/issues/${issueNum}`;
                const proxyUrl = `https://corsproxy.io/?${encodeURIComponent(issueUrl)}`;
                
                const response = await fetch(proxyUrl);
                if (response.ok) {
                    const html = await response.text();
                    
                    // Look for project status in issue page
                    const statusMatch = html.match(/Project[\s\S]*?Status[:\s]*<[^>]*>([^<]+)</i);
                    if (statusMatch) {
                        const status = statusMatch[1].trim();
                        const normalized = statusNormalizationMap[status.toLowerCase()] || status;
                        statusMap.set(issueNum, normalized);
                        console.log(`Issue #${issueNum}: ${status} -> ${normalized}`);
                    }
                }
            } catch (error) {
                console.error(`Error fetching issue #${issueNum}:`, error);
            }
        }
        
        return statusMap;
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
                const projectStatuses = await fetchProjectBoardStatuses();
                
                if (projectStatuses.size === 0) {
                    console.warn('No project statuses parsed, falling back to label-based status');
                    return issues;
                }
                
                // Apply statuses from project board
                const issuesWithStatus = issues.map(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
                    if (projectStatus) {
                        console.log(`Issue #${issue.number}: Project board status "${projectStatus}"`);
                        return {
                            ...issue,
                            projectStatus: projectStatus
                        };
                    } else {
                        // Keep original status or default to Backlog
                        return {
                            ...issue,
                            projectStatus: issue.projectStatus || 'Backlog'
                        };
                    }
                });
                
                // Log status distribution
                const statusDist = {};
                issuesWithStatus.forEach(issue => {
                    statusDist[issue.projectStatus] = (statusDist[issue.projectStatus] || 0) + 1;
                });
                console.log('Status distribution:', statusDist);
                
                return issuesWithStatus;
                
            } catch (error) {
                console.error('Error in fetchProjectIssues override:', error);
                return originalFetch();
            }
        };
        
        fixApplied = true;
        
        // Reload projects
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects with HTML parser...');
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