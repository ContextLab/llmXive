// Enhanced fix for GitHub Project Board status - v2

window.projectBoardFixV2 = {
    // Cache for project data
    cache: null,
    cacheTime: null,
    cacheDuration: 5 * 60 * 1000, // 5 minutes
    
    // Debug mode
    debug: true,
    
    // Fetch project board data with better error handling
    async fetchProjectBoardData() {
        // Check cache first
        if (this.cache && this.cacheTime && (Date.now() - this.cacheTime < this.cacheDuration)) {
            if (this.debug) console.log('Using cached project data');
            return this.cache;
        }
        
        const query = `
            query {
                organization(login: "ContextLab") {
                    projectV2(number: 13) {
                        title
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
            if (this.debug) console.log('Fetching fresh project board data...');
            
            // Try with auth token first if available
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json'
            };
            
            if (window.githubAuth?.token) {
                headers['Authorization'] = `Bearer ${window.githubAuth.token}`;
                if (this.debug) console.log('Using authenticated request');
            } else {
                if (this.debug) console.log('Using unauthenticated request');
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers,
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                console.error('GraphQL request failed with status:', response.status);
                return null;
            }
            
            const data = await response.json();
            
            if (data.errors) {
                console.error('GraphQL errors:', data.errors);
                // Try to continue if we have partial data
            }
            
            const projectItems = data.data?.organization?.projectV2?.items?.nodes;
            
            if (!projectItems) {
                console.error('No project items found in response');
                return null;
            }
            
            if (this.debug) {
                console.log(`Found ${projectItems.length} items in project`);
            }
            
            // Build status map
            const statusMap = new Map();
            let foundCount = 0;
            
            projectItems.forEach(item => {
                if (item.content?.number) {
                    const issueNumber = item.content.number;
                    
                    // Find Status field
                    let status = null;
                    for (const fieldValue of item.fieldValues.nodes) {
                        if (fieldValue.field?.name === 'Status' && fieldValue.name) {
                            status = fieldValue.name;
                            foundCount++;
                            break;
                        }
                    }
                    
                    if (status) {
                        statusMap.set(issueNumber, status);
                        if (this.debug && issueNumber === 21) {
                            console.log(`Issue #21 status: ${status}`);
                        }
                    }
                }
            });
            
            if (this.debug) {
                console.log(`Found status for ${foundCount} issues`);
                
                // Show status distribution
                const distribution = {};
                statusMap.forEach(status => {
                    distribution[status] = (distribution[status] || 0) + 1;
                });
                console.log('Status distribution:', distribution);
            }
            
            // Cache the result
            this.cache = statusMap;
            this.cacheTime = Date.now();
            
            return statusMap;
            
        } catch (error) {
            console.error('Error fetching project board data:', error);
            return null;
        }
    },
    
    // Apply the fix
    async applyFix() {
        if (!window.githubAPI || !window.ui) {
            console.warn('GitHub API or UI not ready');
            return;
        }
        
        console.log('Applying Project Board Fix v2...');
        
        // Override the fetchIssues method
        const originalFetchIssues = window.githubAPI.fetchIssues.bind(window.githubAPI);
        
        window.githubAPI.fetchIssues = async function() {
            const issues = await originalFetchIssues();
            
            if (window.projectBoardFixV2.debug) {
                console.log(`Fetched ${issues.length} issues from GitHub API`);
            }
            
            // Fetch project board data
            const projectStatusMap = await window.projectBoardFixV2.fetchProjectBoardData();
            
            if (!projectStatusMap) {
                console.warn('Could not fetch project board data, using label-based status');
                return issues;
            }
            
            // Update issues with project board status
            const updatedIssues = issues.map(issue => {
                const boardStatus = projectStatusMap.get(issue.number);
                
                if (boardStatus) {
                    if (window.projectBoardFixV2.debug && issue.number === 21) {
                        console.log(`Updating issue #21 status from "${issue.projectStatus}" to "${boardStatus}"`);
                    }
                    
                    return {
                        ...issue,
                        projectStatus: boardStatus
                    };
                } else {
                    // Keep existing status if not found in project
                    if (window.projectBoardFixV2.debug) {
                        console.log(`Issue #${issue.number} not found in project board, keeping status: ${issue.projectStatus}`);
                    }
                    return issue;
                }
            });
            
            return updatedIssues;
        };
        
        // Also fix the renderProjects method to handle status properly
        const originalRenderProjects = window.ui.renderProjects.bind(window.ui);
        
        window.ui.renderProjects = function() {
            if (window.projectBoardFixV2.debug) {
                // Log status distribution before rendering
                const statusCounts = {};
                this.filteredProjects.forEach(p => {
                    const status = p.projectStatus || 'Unknown';
                    statusCounts[status] = (statusCounts[status] || 0) + 1;
                });
                console.log('Projects by status before rendering:', statusCounts);
            }
            
            // Call original render method
            originalRenderProjects.call(this);
        };
        
        console.log('Project Board Fix v2 applied successfully');
        
        // Trigger a reload to apply the fix
        if (window.ui.loadProjects) {
            console.log('Reloading projects with fix...');
            await window.ui.loadProjects();
        }
    }
};