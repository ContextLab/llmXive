// Fix for fetching actual GitHub Project Board status

window.projectBoardFix = {
    // Cache project data to avoid excessive API calls
    projectCache: new Map(),
    cacheTimeout: 5 * 60 * 1000, // 5 minutes
    
    // Fetch all project items in one query (more efficient)
    async fetchProjectBoardData() {
        const cacheKey = 'project_13_data';
        const cached = this.projectCache.get(cacheKey);
        
        if (cached && (Date.now() - cached.timestamp < this.cacheTimeout)) {
            return cached.data;
        }
        
        const query = `
            query {
                organization(login: "ContextLab") {
                    projectV2(number: 13) {
                        items(first: 100) {
                            nodes {
                                id
                                content {
                                    ... on Issue {
                                        number
                                        title
                                    }
                                }
                                fieldValues(first: 10) {
                                    nodes {
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
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // No auth needed for public projects
                },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                console.error('GraphQL request failed:', response.status);
                return null;
            }
            
            const data = await response.json();
            
            if (data.errors) {
                console.error('GraphQL errors:', data.errors);
                return null;
            }
            
            const projectData = data.data?.organization?.projectV2?.items?.nodes || [];
            
            // Create a map of issue number to status
            const statusMap = new Map();
            
            for (const item of projectData) {
                if (item.content?.number) {
                    const statusField = item.fieldValues.nodes.find(
                        fv => fv.field?.name === 'Status'
                    );
                    if (statusField) {
                        statusMap.set(item.content.number, statusField.name);
                    }
                }
            }
            
            // Cache the result
            this.projectCache.set(cacheKey, {
                timestamp: Date.now(),
                data: statusMap
            });
            
            return statusMap;
            
        } catch (error) {
            console.error('Error fetching project board data:', error);
            return null;
        }
    },
    
    // Apply fix to the GitHub API
    applyFix() {
        if (!window.githubAPI) {
            console.warn('GitHub API not found');
            return;
        }
        
        // Override fetchIssues to include real project board status
        const originalFetchIssues = window.githubAPI.fetchIssues.bind(window.githubAPI);
        
        window.githubAPI.fetchIssues = async function() {
            // First get the issues
            const issues = await originalFetchIssues();
            
            // Then fetch project board data
            const projectStatusMap = await window.projectBoardFix.fetchProjectBoardData();
            
            if (projectStatusMap) {
                // Update issues with actual project board status
                return issues.map(issue => {
                    const boardStatus = projectStatusMap.get(issue.number);
                    if (boardStatus) {
                        return {
                            ...issue,
                            projectStatus: boardStatus
                        };
                    }
                    return issue;
                });
            }
            
            // If we couldn't get project data, return issues as-is
            return issues;
        };
        
        console.log('Project board fix applied');
    }
};