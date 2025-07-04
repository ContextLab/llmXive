// Simple fix to bypass label-based status completely

(function() {
    console.log('Applying simple project board fix...');
    
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
        // Wait for githubAPI to be available
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('Overriding getStatusFromLabels to prevent Backlog default...');
        
        // Override getStatusFromLabels to return null instead of 'Backlog'
        window.api.getStatusFromLabels = function(labels) {
            console.log('getStatusFromLabels called with:', labels.map(l => l.name));
            
            const statusMap = {
                'backlog': 'Backlog',
                'ready': 'Ready',
                'in progress': 'In Progress',
                'in-progress': 'In Progress',
                'in review': 'In Review',
                'in-review': 'In Review',
                'done': 'Done',
                'completed': 'Done'
            };
            
            // Check for exact matches
            for (const label of labels) {
                const labelName = label.name.toLowerCase().trim();
                if (statusMap[labelName]) {
                    console.log(`Found status label: ${label.name} -> ${statusMap[labelName]}`);
                    return statusMap[labelName];
                }
            }
            
            // NO DEFAULT - return null if no status label found
            console.log('No status label found, returning null (not defaulting to Backlog)');
            return null;
        };
        
        // Also override the renderProjects to handle null status
        await waitFor(() => window.ui && window.ui.renderProjects);
        
        const originalRender = window.ui.renderProjects.bind(window.ui);
        
        window.ui.renderProjects = function() {
            console.log('=== RENDER PROJECTS ===');
            
            // First, let's see what statuses we have
            const statusDist = {};
            this.filteredProjects.forEach(p => {
                const status = p.projectStatus;
                statusDist[status || 'null'] = (statusDist[status || 'null'] || 0) + 1;
            });
            console.log('Project statuses before render:', statusDist);
            
            // Group projects by status
            const grouped = {};
            this.columns.forEach(col => grouped[col] = []);
            
            // Add "Unknown" column for null statuses
            grouped['Unknown'] = [];
            
            this.filteredProjects.forEach(project => {
                const status = project.projectStatus;
                
                if (status && grouped[status]) {
                    grouped[status].push(project);
                } else if (!status) {
                    // Put null status in Unknown
                    grouped['Unknown'].push(project);
                    console.log(`Issue #${project.number} has null status`);
                } else {
                    console.warn(`Issue #${project.number} has status "${status}" which doesn't match any column`);
                }
            });
            
            // Log distribution
            Object.entries(grouped).forEach(([col, projects]) => {
                if (projects.length > 0) {
                    console.log(`Column "${col}": ${projects.length} projects`);
                }
            });
            
            // Call original render
            originalRender.call(this);
        };
        
        // Trigger reload
        if (window.ui && window.ui.loadProjects) {
            console.log('Reloading projects...');
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