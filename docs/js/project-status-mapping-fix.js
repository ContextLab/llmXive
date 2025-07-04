// Fix for case-sensitive project board status mapping
(function() {
    console.log('Applying project status mapping fix...');
    
    // Create a normalization map
    const statusNormalizationMap = {
        'backlog': 'Backlog',
        'ready': 'Ready',
        'in progress': 'In Progress',
        'in review': 'In Review',
        'done': 'Done'
    };
    
    // Wait for components to load
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
        // Wait for the project board direct fix to load
        await waitFor(() => window.projectBoardDirectFix);
        
        // Override the getProjectStatuses method to normalize statuses
        const originalGetStatuses = window.projectBoardDirectFix.getProjectStatuses.bind(window.projectBoardDirectFix);
        
        window.projectBoardDirectFix.getProjectStatuses = async function() {
            console.log('Getting project statuses with normalization...');
            
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
                }
                
                const response = await fetch('https://api.github.com/graphql', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({ query })
                });
                
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
                                
                                if (item.content.number === 21) {
                                    console.log(`Issue #21: Raw status "${statusField.name}" -> Normalized "${normalizedStatus}"`);
                                }
                            }
                        }
                    });
                }
                
                console.log('Normalized project status map:', Array.from(statusMap.entries()));
                return statusMap;
                
            } catch (error) {
                console.error('Error getting project statuses:', error);
                return new Map();
            }
        };
        
        // Trigger a reload
        if (window.ui?.loadProjects) {
            console.log('Reloading projects with status normalization...');
            await window.ui.loadProjects();
        }
    }
    
    // Apply fix when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(applyFix, 2500); // Wait a bit longer for other fixes to load
        });
    } else {
        setTimeout(applyFix, 2500);
    }
})();