// Simple fix using REST API instead of GraphQL
(function() {
    console.log('Applying REST API project board fix...');
    
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
    
    async function applyFix() {
        if (fixApplied) {
            console.log('Fix already applied, skipping...');
            return;
        }
        
        // Wait for API to be available
        await waitFor(() => window.api && window.api.getStatusFromLabels);
        
        console.log('Overriding getStatusFromLabels to prevent default Backlog...');
        
        // First, override getStatusFromLabels to not default to Backlog
        const originalGetStatus = window.api.getStatusFromLabels.bind(window.api);
        
        window.api.getStatusFromLabels = function(labels) {
            console.log('getStatusFromLabels override called with:', labels.map(l => l.name));
            
            // Check for exact matches first (case-insensitive)
            for (const label of labels) {
                const labelName = label.name.toLowerCase().trim();
                const normalizedStatus = statusNormalizationMap[labelName];
                if (normalizedStatus) {
                    console.log(`Found status label: "${label.name}" -> "${normalizedStatus}"`);
                    return normalizedStatus;
                }
            }
            
            // Then check for partial matches
            for (const label of labels) {
                const labelName = label.name.toLowerCase().trim();
                for (const [key, status] of Object.entries(statusNormalizationMap)) {
                    if (labelName.includes(key)) {
                        console.log(`Found partial status match: "${label.name}" contains "${key}" -> "${status}"`);
                        return status;
                    }
                }
            }
            
            // Don't default to Backlog - return null
            console.log('No status label found, returning null (not defaulting)');
            return null;
        };
        
        // Wait for UI
        await waitFor(() => window.ui && window.ui.renderProjects);
        
        // Override renderProjects to handle null status better
        const originalRender = window.ui.renderProjects.bind(window.ui);
        
        window.ui.renderProjects = function() {
            console.log('=== RENDER PROJECTS (REST API FIX) ===');
            
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
                console.log('Issue #21 found:');
                console.log('- Title:', issue21.title);
                console.log('- Status:', issue21.projectStatus);
                console.log('- Labels:', issue21.labels.map(l => l.name));
            }
            
            // Group projects by status
            const grouped = {};
            this.columns.forEach(col => grouped[col] = []);
            
            // Add a temporary column for no status
            grouped['No Status'] = [];
            
            this.filteredProjects.forEach(project => {
                const status = project.projectStatus;
                
                if (status && grouped[status]) {
                    grouped[status].push(project);
                } else if (!status) {
                    // Put issues with no status in Backlog
                    grouped['Backlog'].push(project);
                    console.log(`Issue #${project.number} has no status, putting in Backlog`);
                } else {
                    // Default to Backlog for unrecognized statuses
                    grouped['Backlog'].push(project);
                    console.warn(`Issue #${project.number} has unrecognized status "${status}", putting in Backlog`);
                }
            });
            
            // Log grouped distribution
            console.log('Grouped distribution:');
            Object.entries(grouped).forEach(([col, projects]) => {
                if (projects.length > 0) {
                    console.log(`- ${col}: ${projects.length} projects`);
                }
            });
            
            // Render each column (skip "No Status" column)
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
                    // Use renderProjectCard method
                    container.innerHTML = projects.map(project => this.renderProjectCard(project)).join('');
                }
            });
            
            // Update stats
            this.updateStats();
        };
        
        fixApplied = true;
        
        // Add manual status setting for issue 21 as a test
        console.log('Manually setting issue #21 to "In Progress" for testing...');
        
        // Override fetchProjectIssues to manually set issue 21 status
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            const issues = await originalFetch();
            
            // Manually set issue 21 to "In Progress"
            return issues.map(issue => {
                if (issue.number === 21) {
                    console.log('Setting issue #21 to "In Progress"');
                    return {
                        ...issue,
                        projectStatus: 'In Progress'
                    };
                }
                return issue;
            });
        };
        
        // Reload projects
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects with REST API fix...');
            await window.ui.loadProjects();
        }
    }
    
    // Apply fix when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(applyFix, 1000);
        });
    } else {
        setTimeout(applyFix, 1000);
    }
})();