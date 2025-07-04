// Fix for renderProjects to prevent defaulting to Backlog
(function() {
    console.log('Applying renderProjects fix...');
    
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
        await waitFor(() => window.ui && window.ui.renderProjects);
        
        console.log('Overriding renderProjects to fix default Backlog assignment...');
        
        const originalRender = window.ui.renderProjects.bind(window.ui);
        
        window.ui.renderProjects = function() {
            console.log('=== RENDER PROJECTS (FIXED) ===');
            
            // Log status distribution
            const statusDist = {};
            this.filteredProjects.forEach(p => {
                const status = p.projectStatus;
                statusDist[status || 'NO_STATUS'] = (statusDist[status || 'NO_STATUS'] || 0) + 1;
            });
            console.log('Project status distribution:', statusDist);
            
            // Find issue 21
            const issue21 = this.filteredProjects.find(p => p.number === 21);
            if (issue21) {
                console.log('Issue #21 status before render:', issue21.projectStatus);
            }
            
            // Group projects by status WITHOUT defaulting to Backlog
            const grouped = {};
            this.columns.forEach(col => grouped[col] = []);
            
            this.filteredProjects.forEach(project => {
                const status = project.projectStatus; // NO DEFAULT!
                
                if (status && grouped[status]) {
                    grouped[status].push(project);
                } else if (!status) {
                    console.warn(`Issue #${project.number} has no status, skipping...`);
                } else if (!grouped[status]) {
                    console.warn(`Issue #${project.number} has status "${status}" which is not a valid column`);
                }
            });
            
            // Log grouped distribution
            console.log('Grouped distribution:');
            Object.entries(grouped).forEach(([col, projects]) => {
                console.log(`- ${col}: ${projects.length} projects`);
                if (col === 'In Progress') {
                    console.log('  Issues in "In Progress":', projects.map(p => `#${p.number}`).join(', '));
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
                    container.innerHTML = projects.map(project => this.renderProjectCard(project)).join('');
                }
            });
            
            // Update stats
            this.updateStats();
        };
        
        // Also fix renderProjectCard to use createProjectCard
        window.ui.renderProjectCard = window.ui.createProjectCard;
    }
    
    // Apply fix when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(applyFix, 2000);
        });
    } else {
        setTimeout(applyFix, 2000);
    }
})();