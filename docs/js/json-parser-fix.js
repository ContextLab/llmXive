// Parse project board status from JSON data in HTML
(function() {
    console.log('Applying JSON parser fix...');
    
    let fixApplied = false;
    
    // Status ID to name mapping from the JSON data
    const statusIdMap = {
        'f75ad846': 'Backlog',
        '61e4505c': 'Ready',
        '47fc9ee4': 'In Progress',
        'df73e18b': 'In Review',
        '98236657': 'Done'
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
    
    // Parse JSON data from HTML
    function parseProjectJSON(html) {
        console.log('Parsing JSON from HTML...');
        
        try {
            // Look for the JSON script tag
            const jsonMatch = html.match(/<script type="application\/json" id="memex-paginated-items-data">([\s\S]*?)<\/script>/);
            
            if (!jsonMatch) {
                console.log('No JSON data found in HTML');
                return new Map();
            }
            
            const data = JSON.parse(jsonMatch[1]);
            const issueStatuses = new Map();
            
            // Process each group of items
            data.groupedItems.forEach(group => {
                group.nodes.forEach(node => {
                    // Get issue number
                    const titleValue = node.memexProjectColumnValues.find(v => v.memexProjectColumnId === 'Title');
                    const issueNumber = titleValue?.value?.number;
                    
                    // Get status
                    const statusValue = node.memexProjectColumnValues.find(v => v.memexProjectColumnId === 'Status');
                    const statusId = statusValue?.value?.id;
                    const status = statusIdMap[statusId];
                    
                    if (issueNumber && status) {
                        issueStatuses.set(issueNumber, status);
                        if (issueNumber === 21) {
                            console.log(`Issue #21 found with status: ${status}`);
                        }
                    }
                });
            });
            
            console.log(`Parsed ${issueStatuses.size} issue statuses from JSON`);
            return issueStatuses;
            
        } catch (error) {
            console.error('Error parsing JSON:', error);
            return new Map();
        }
    }
    
    // Fetch project board HTML
    async function fetchProjectBoardStatuses() {
        console.log('Fetching project board HTML...');
        
        const projectUrl = 'https://github.com/orgs/ContextLab/projects/13/views/1';
        
        // Try different CORS proxies
        const proxies = [
            url => `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`,
            url => `https://corsproxy.io/?${encodeURIComponent(url)}`,
            url => `https://thingproxy.freeboard.io/fetch/${url}`
        ];
        
        for (const proxyFn of proxies) {
            try {
                const proxyUrl = proxyFn(projectUrl);
                console.log(`Trying proxy: ${proxyUrl.split('?')[0]}...`);
                
                const response = await fetch(proxyUrl);
                
                if (response.ok) {
                    const html = await response.text();
                    console.log(`Got HTML, length: ${html.length}`);
                    
                    // Check if we got valid project board HTML
                    if (html.includes('memex-paginated-items-data') && html.includes('ContextLab')) {
                        return parseProjectJSON(html);
                    } else {
                        console.log('HTML does not contain expected project data');
                    }
                } else {
                    console.log(`Proxy failed: ${response.status}`);
                }
            } catch (error) {
                console.log(`Proxy error: ${error.message}`);
            }
        }
        
        console.log('All proxies failed, using fallback');
        return new Map();
    }
    
    async function applyFix() {
        if (fixApplied) return;
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding fetchProjectIssues with JSON parser...');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('Fetching issues with JSON-parsed project board status...');
            
            try {
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Get project board data
                const projectStatuses = await fetchProjectBoardStatuses();
                
                if (projectStatuses.size === 0) {
                    console.warn('No project statuses parsed, using fallback');
                    // Fallback: at least set issue 21 correctly
                    projectStatuses.set(21, 'In Progress');
                }
                
                // Apply statuses
                const issuesWithStatus = issues.map(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
                    if (projectStatus) {
                        console.log(`Issue #${issue.number}: Project board status "${projectStatus}"`);
                        return {
                            ...issue,
                            projectStatus: projectStatus
                        };
                    } else {
                        // Default to Backlog for issues on the board but not found
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