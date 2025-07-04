// Direct fix for project board status - no label fallback

window.projectBoardDirectFix = {
    debug: true,
    
    // Test the GraphQL query directly
    async testDirectQuery() {
        console.log('=== TESTING DIRECT PROJECT BOARD QUERY ===');
        
        // Simple query to get project items with status
        const query = `
            query {
                organization(login: "ContextLab") {
                    projectV2(number: 13) {
                        title
                        items(first: 100) {
                            nodes {
                                content {
                                    ... on Issue {
                                        number
                                        title
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
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            console.log('Raw GraphQL response:', data);
            
            if (data.data?.organization?.projectV2?.items?.nodes) {
                const items = data.data.organization.projectV2.items.nodes;
                console.log(`Found ${items.length} items in project`);
                
                // Find issue 21
                const issue21 = items.find(item => item.content?.number === 21);
                if (issue21) {
                    console.log('Issue 21 data:', issue21);
                    console.log('Issue 21 field values:', issue21.fieldValues.nodes);
                }
                
                // Show all statuses
                console.log('\n=== ALL ISSUE STATUSES ===');
                items.forEach(item => {
                    if (item.content?.number) {
                        const statusField = item.fieldValues.nodes.find(
                            fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                                  fv.field?.name === 'Status'
                        );
                        console.log(`Issue #${item.content.number}: ${statusField?.name || 'NO STATUS FOUND'}`);
                    }
                });
            }
            
        } catch (error) {
            console.error('Direct query error:', error);
        }
    },
    
    // Apply a simpler, more direct fix
    async applyFix() {
        console.log('Applying Direct Project Board Fix...');
        
        // First run the test
        await this.testDirectQuery();
        
        // Override fetchIssues with direct project board lookup
        if (window.githubAPI) {
            const originalFetch = window.githubAPI.fetchIssues.bind(window.githubAPI);
            
            window.githubAPI.fetchIssues = async function() {
                console.log('Fetching issues with direct project board status...');
                
                // Get issues first
                const issues = await originalFetch();
                console.log(`Got ${issues.length} issues from API`);
                
                // Now get project board data
                const projectStatuses = await window.projectBoardDirectFix.getProjectStatuses();
                
                // Apply statuses directly
                const updatedIssues = issues.map(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
                    if (projectStatus) {
                        console.log(`Issue #${issue.number}: Setting status to "${projectStatus}" (was: "${issue.projectStatus}")`);
                        return {
                            ...issue,
                            projectStatus: projectStatus
                        };
                    } else {
                        console.log(`Issue #${issue.number}: No project status found, current status: "${issue.projectStatus}"`);
                        // Don't default to Backlog - keep whatever was there
                        return issue;
                    }
                });
                
                return updatedIssues;
            };
        }
        
        // Also override the column assignment to not default to Backlog
        if (window.ui) {
            const originalRender = window.ui.renderProjects.bind(window.ui);
            
            window.ui.renderProjects = function() {
                console.log('=== RENDERING PROJECTS ===');
                
                // Log what we're about to render
                const statusCount = {};
                this.filteredProjects.forEach(p => {
                    const status = p.projectStatus || 'NO_STATUS';
                    statusCount[status] = (statusCount[status] || 0) + 1;
                    
                    if (p.number === 21) {
                        console.log(`Issue #21 projectStatus before render: "${p.projectStatus}"`);
                    }
                });
                console.log('Status distribution:', statusCount);
                
                // Group projects by status WITHOUT defaulting to Backlog
                const grouped = {};
                this.columns.forEach(col => grouped[col] = []);
                
                this.filteredProjects.forEach(project => {
                    const status = project.projectStatus;
                    
                    // Only add to a column if we have a matching status
                    if (status && grouped[status]) {
                        grouped[status].push(project);
                    } else {
                        console.warn(`Issue #${project.number} has status "${status}" which doesn't match any column`);
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
                        container.innerHTML = projects.map(project => this.createProjectCard(project)).join('');
                    }
                });
                
                // Update stats
                this.updateStats();
            };
        }
        
        // Reload projects
        if (window.ui?.loadProjects) {
            console.log('Reloading projects with direct fix...');
            await window.ui.loadProjects();
        }
    },
    
    // Get project statuses as a Map
    async getProjectStatuses() {
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
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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
                            statusMap.set(item.content.number, statusField.name);
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
};

// Auto-apply on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            window.projectBoardDirectFix.applyFix();
        }, 2000); // Wait for other scripts to load
    });
} else {
    setTimeout(() => {
        window.projectBoardDirectFix.applyFix();
    }, 2000);
}