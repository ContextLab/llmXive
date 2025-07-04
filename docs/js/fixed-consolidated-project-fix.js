// Fixed consolidated fix for project board status issues
(function() {
    console.log('Applying FIXED consolidated project board fix...');
    
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
                'Accept': 'application/vnd.github+json'
            };
            
            // Add auth if available from githubAuth
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                const authHeaders = window.githubAuth.getAuthHeaders();
                Object.assign(headers, authHeaders);
                console.log('Using authenticated request for project board');
            } else {
                console.log('Making unauthenticated request - may hit rate limits');
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
            console.log('GraphQL response data:', data);
            
            const statusMap = new Map();
            
            if (data.errors) {
                console.error('GraphQL errors:', data.errors);
                return statusMap;
            }
            
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
                                console.log(`Issue #21: Raw status "${statusField.name}" -> Normalized "${normalizedStatus}"`);
                            }
                        }
                    }
                });
            } else {
                console.error('No project data found in response');
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
        
        // Fix the renderProjects method
        await waitFor(() => window.ui && window.ui.renderProjects);
        
        const originalRender = window.ui.renderProjects.bind(window.ui);
        
        window.ui.renderProjects = function() {
            console.log('=== RENDER PROJECTS (FIXED v2) ===');
            
            // Log status distribution
            const statusDist = {};
            this.filteredProjects.forEach(p => {
                const status = p.projectStatus || 'NO_STATUS';
                statusDist[status] = (statusDist[status] || 0) + 1;
            });
            console.log('Project status distribution:', statusDist);
            
            // Find issue 21
            const issue21 = this.filteredProjects.find(p => p.number === 21);
            if (issue21) {
                console.log('Issue #21 status before render:', issue21.projectStatus);
            }
            
            // Group projects by status
            const grouped = {};
            this.columns.forEach(col => grouped[col] = []);
            
            this.filteredProjects.forEach(project => {
                const status = project.projectStatus || 'Backlog'; // Default to Backlog if no status
                if (grouped[status]) {
                    grouped[status].push(project);
                } else {
                    console.warn(`Issue #${project.number} has status "${status}" which is not a valid column`);
                }
            });
            
            // Render each column
            this.columns.forEach(column => {
                const container = document.getElementById(`column-${column.replace(/\s+/g, '-')}`);
                const count = document.getElementById(`count-${column.replace(/\s+/g, '-')}`);
                const projects = grouped[column] || [];
                
                count.textContent = projects.length;
                
                if (projects.length === 0) {
                    container.innerHTML = `
                        <div class="empty-column">
                            <i class="fas fa-inbox"></i>
                            <p>No projects</p>
                        </div>
                    `;
                } else {
                    // Use createProjectCard method
                    container.innerHTML = projects.map(project => this.createProjectCard(project)).join('');
                }
            });
            
            // Update stats
            this.updateStats();
        };
        
        fixApplied = true;
        
        // Reload projects if UI is ready
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects with fixed consolidated fix...');
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