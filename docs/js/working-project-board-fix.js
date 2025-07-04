// Working fix using the same GraphQL query that works in test script
(function() {
    console.log('Applying working project board fix...');
    
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
    
    // Get project statuses using the exact query that works in our test
    async function getProjectStatuses() {
        const query = `
            query {
                organization(login: "ContextLab") {
                    projectV2(number: 13) {
                        items(first: 100) {
                            nodes {
                                content {
                                    ... on Issue {
                                        number
                                    }
                                }
                                fieldValues(first: 20) {
                                    nodes {
                                        __typename
                                        ... on ProjectV2ItemFieldSingleSelectValue {
                                            name
                                            field {
                                                ... on ProjectV2SingleSelectField {
                                                    name
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        `;
        
        try {
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json'
            };
            
            // Add authentication if available
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
                console.log('Using authenticated request');
            } else {
                console.log('Making unauthenticated request (may hit rate limits)');
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query })
            });
            
            console.log('GraphQL response status:', response.status);
            
            if (!response.ok) {
                const text = await response.text();
                console.error('GraphQL request failed:', response.status, text);
                return new Map();
            }
            
            const data = await response.json();
            
            if (data.errors) {
                console.error('GraphQL errors:', data.errors);
                return new Map();
            }
            
            const statusMap = new Map();
            
            if (data.data?.organization?.projectV2?.items?.nodes) {
                const items = data.data.organization.projectV2.items.nodes;
                console.log(`Found ${items.length} items in project board`);
                
                items.forEach(item => {
                    if (item.content?.number) {
                        const statusField = item.fieldValues.nodes.find(
                            fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                                  fv.field?.name === 'Status'
                        );
                        
                        if (statusField?.name) {
                            // Normalize the status name
                            const normalizedStatus = statusNormalizationMap[statusField.name.toLowerCase()] || statusField.name;
                            statusMap.set(item.content.number, normalizedStatus);
                            
                            if (item.content.number === 21) {
                                console.log(`Issue #21: "${statusField.name}" -> "${normalizedStatus}"`);
                            }
                        }
                    }
                });
                
                console.log(`Status map has ${statusMap.size} entries`);
                
                // Log first few entries
                const entries = Array.from(statusMap.entries()).slice(0, 5);
                console.log('Sample statuses:', entries);
            }
            
            return statusMap;
            
        } catch (error) {
            console.error('Error getting project statuses:', error);
            return new Map();
        }
    }
    
    async function applyFix() {
        if (fixApplied) return;
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding fetchProjectIssues...');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('Fetching issues with project board status...');
            
            try {
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Get project board data
                const projectStatuses = await getProjectStatuses();
                
                if (projectStatuses.size === 0) {
                    console.error('No project board statuses fetched!');
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