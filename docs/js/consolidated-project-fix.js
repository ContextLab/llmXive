// Consolidated fix for project board status issues
(function() {
    console.log('Applying consolidated project board fix...');
    
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
    
    // Get project statuses from GitHub project board
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
            // Get auth headers if available
            const headers = {
                'Content-Type': 'application/json',
            };
            
            // Add auth if available from githubAuth
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                const authHeaders = window.githubAuth.getAuthHeaders();
                Object.assign(headers, authHeaders);
                console.log('Using authenticated request for project board');
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                console.error('GraphQL request failed:', response.status, response.statusText);
                return new Map();
            }
            
            const data = await response.json();
            const statusMap = new Map();
            
            if (data.data?.organization?.projectV2?.items?.nodes) {
                data.data.organization.projectV2.items.nodes.forEach(item => {
                    if (item.content?.number) {
                        const statusField = item.fieldValues.nodes.find(
                            fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                                  fv.field?.name === 'Status'
                        );
                        
                        if (statusField?.name) {
                            // Normalize the status name
                            const normalizedStatus = statusNormalizationMap[statusField.name.toLowerCase()] || statusField.name;
                            statusMap.set(item.content.number, normalizedStatus);
                        }
                    }
                });
            }
            
            console.log('Project status map:', Array.from(statusMap.entries()));
            return statusMap;
            
        } catch (error) {
            console.error('Error getting project statuses:', error);
            return new Map();
        }
    }
    
    async function applyFix() {
        if (fixApplied) {
            console.log('Fix already applied, skipping...');
            return;
        }
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding fetchProjectIssues with project board integration...');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('Fetching issues with project board status...');
            
            try {
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Get project board data
                const projectStatuses = await getProjectStatuses();
                
                // Apply statuses
                const updatedIssues = issues.map(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
                    if (projectStatus) {
                        console.log(`Issue #${issue.number}: Project board status "${projectStatus}"`);
                        return {
                            ...issue,
                            projectStatus: projectStatus
                        };
                    } else {
                        // Keep label-based status if no project board status
                        console.log(`Issue #${issue.number}: No project board status, using label status "${issue.projectStatus}"`);
                        return issue;
                    }
                });
                
                return updatedIssues;
                
            } catch (error) {
                console.error('Error in fetchProjectIssues override:', error);
                // Fall back to original behavior
                return originalFetch();
            }
        };
        
        fixApplied = true;
        
        // Reload projects if UI is ready
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects with consolidated fix...');
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