/**
 * Enhanced Dashboard Component for llmXive Web Interface
 * 
 * Displays project data from the corrected database with proper date attributions
 */

class EnhancedDashboard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.dataManager = window.ProjectDataManager;
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Enhanced Dashboard...');
        
        // Show loading state
        this.showLoading();
        
        try {
            // Load project data
            const loaded = await this.dataManager.loadData();
            if (!loaded) {
                throw new Error('Failed to load project data');
            }
            
            // Render dashboard
            await this.render();
            console.log('✅ Enhanced Dashboard initialized successfully');
            
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.showError(error.message);
        }
    }

    showLoading() {
        this.container.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <h3>Loading llmXive Data...</h3>
                <p>Fetching project database with corrected dates and attributions</p>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="error-container">
                <h3>⚠️ Error Loading Dashboard</h3>
                <p>${message}</p>
                <button onclick="location.reload()">Retry</button>
            </div>
        `;
    }

    async render() {
        const stats = this.dataManager.getDashboardStats();
        const enhancedProjects = this.dataManager.getEnhancedProjects();
        const recentProjects = this.dataManager.getRecentProjects();
        const projectsWithIssues = this.dataManager.getProjectsWithIssues();
        
        this.container.innerHTML = `
            <div class="enhanced-dashboard">
                <header class="dashboard-header">
                    <h1>🧬 llmXive Research Dashboard</h1>
                    <div class="date-range">
                        <span class="label">Project Date Range:</span>
                        <span class="value">${stats.dateRange}</span>
                    </div>
                </header>

                <!-- Statistics Cards -->
                <div class="stats-grid">
                    <div class="stat-card total-projects">
                        <div class="stat-value">${stats.totalProjects}</div>
                        <div class="stat-label">Total Projects</div>
                        <div class="stat-detail">All research projects in database</div>
                    </div>
                    
                    <div class="stat-card enhanced-projects">
                        <div class="stat-value">${stats.enhancedProjects}</div>
                        <div class="stat-label">🤖 Enhanced by Gemini</div>
                        <div class="stat-detail">Content completed & enhanced</div>
                    </div>
                    
                    <div class="stat-card completeness">
                        <div class="stat-value">${stats.averageCompleteness}%</div>
                        <div class="stat-label">Average Completeness</div>
                        <div class="stat-detail">Across all projects</div>
                    </div>
                    
                    <div class="stat-card issues">
                        <div class="stat-value">${stats.projectsWithIssues}</div>
                        <div class="stat-label">⚠️ Need Attention</div>
                        <div class="stat-detail">Projects with open issues</div>
                    </div>
                </div>

                <!-- Enhanced Projects Showcase -->
                <section class="enhanced-showcase">
                    <h2>🌟 Recently Enhanced Projects</h2>
                    <p class="section-description">
                        These projects received significant content enhancement from Google Gemini with 
                        proper methodology, comprehensive literature reviews, and complete technical specifications.
                    </p>
                    <div class="enhanced-projects-grid">
                        ${enhancedProjects.map(project => this.renderEnhancedProjectCard(project)).join('')}
                    </div>
                </section>

                <!-- Field Distribution -->
                <section class="field-distribution">
                    <h2>📊 Projects by Research Field</h2>
                    <div class="field-grid">
                        ${Object.entries(stats.fieldDistribution).map(([field, count]) => 
                            this.renderFieldCard(field, count)
                        ).join('')}
                    </div>
                </section>

                <!-- Recent Activity -->
                <section class="recent-activity">
                    <h2>🕒 Recent Activity (${stats.dateRange})</h2>
                    <div class="activity-list">
                        ${recentProjects.slice(0, 5).map(project => this.renderActivityItem(project)).join('')}
                    </div>
                </section>

                <!-- Issues & Improvements -->
                ${projectsWithIssues.length > 0 ? `
                <section class="issues-section">
                    <h2>⚠️ Projects Needing Attention</h2>
                    <div class="issues-list">
                        ${projectsWithIssues.map(project => this.renderIssueItem(project)).join('')}
                    </div>
                </section>
                ` : ''}

                <!-- Database Info -->
                <section class="database-info">
                    <h2>🗄️ Database Information</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Date Corrections Applied:</strong>
                            All project dates corrected to July 1-7, 2025 timeframe
                        </div>
                        <div class="info-item">
                            <strong>Attribution Fixes:</strong>
                            Proper AI model attributions (TinyLlama, Claude, Gemini)
                        </div>
                        <div class="info-item">
                            <strong>Content Enhancement:</strong>
                            ${stats.enhancedProjects} projects enhanced with comprehensive content
                        </div>
                        <div class="info-item">
                            <strong>Last Updated:</strong>
                            ${new Date().toLocaleString()}
                        </div>
                    </div>
                </section>
            </div>

            <style>
                .enhanced-dashboard {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }

                .dashboard-header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }

                .dashboard-header h1 {
                    margin: 0 0 10px 0;
                    font-size: 2.5rem;
                    font-weight: 700;
                }

                .date-range {
                    font-size: 1.1rem;
                    opacity: 0.9;
                }

                .date-range .label {
                    font-weight: 500;
                }

                .date-range .value {
                    font-weight: 700;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 12px;
                    border-radius: 6px;
                    margin-left: 8px;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }

                .stat-card {
                    background: white;
                    padding: 24px;
                    border-radius: 12px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                    border-left: 5px solid;
                }

                .stat-card.total-projects { border-left-color: #3b82f6; }
                .stat-card.enhanced-projects { border-left-color: #10b981; }
                .stat-card.completeness { border-left-color: #f59e0b; }
                .stat-card.issues { border-left-color: #ef4444; }

                .stat-value {
                    font-size: 3rem;
                    font-weight: 700;
                    margin-bottom: 8px;
                    line-height: 1;
                }

                .stat-label {
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 4px;
                    color: #374151;
                }

                .stat-detail {
                    font-size: 0.9rem;
                    color: #6b7280;
                }

                .enhanced-showcase, .field-distribution, .recent-activity, .issues-section, .database-info {
                    margin-bottom: 40px;
                }

                .enhanced-showcase h2, .field-distribution h2, .recent-activity h2, .issues-section h2, .database-info h2 {
                    font-size: 1.8rem;
                    margin-bottom: 16px;
                    color: #1f2937;
                    border-bottom: 3px solid #e5e7eb;
                    padding-bottom: 8px;
                }

                .section-description {
                    font-size: 1.1rem;
                    color: #6b7280;
                    margin-bottom: 24px;
                    line-height: 1.6;
                }

                .enhanced-projects-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 24px;
                }

                .enhanced-project-card {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    overflow: hidden;
                    transition: transform 0.2s, box-shadow 0.2s;
                }

                .enhanced-project-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 15px rgba(0,0,0,0.15);
                }

                .project-header {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    padding: 20px;
                }

                .project-title {
                    font-size: 1.3rem;
                    font-weight: 600;
                    margin-bottom: 8px;
                    line-height: 1.3;
                }

                .project-field {
                    font-size: 0.9rem;
                    opacity: 0.9;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 4px;
                    display: inline-block;
                }

                .project-body {
                    padding: 20px;
                }

                .project-description {
                    color: #6b7280;
                    margin-bottom: 16px;
                    line-height: 1.5;
                }

                .project-meta {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .meta-item {
                    font-size: 0.9rem;
                }

                .meta-label {
                    font-weight: 600;
                    color: #374151;
                }

                .meta-value {
                    color: #6b7280;
                }

                .completeness-bar {
                    background: #f3f4f6;
                    border-radius: 6px;
                    height: 8px;
                    overflow: hidden;
                    margin-top: 8px;
                }

                .completeness-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #10b981 0%, #059669 100%);
                    transition: width 0.3s ease;
                }

                .enhancement-badge {
                    display: inline-flex;
                    align-items: center;
                    background: #fef3c7;
                    color: #92400e;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    margin-top: 12px;
                }

                .field-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                }

                .field-card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }

                .field-name {
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #374151;
                }

                .field-count {
                    font-size: 2rem;
                    font-weight: 700;
                    color: #3b82f6;
                }

                .activity-list, .issues-list {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }

                .activity-item, .issue-item {
                    padding: 16px 20px;
                    border-bottom: 1px solid #f3f4f6;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .activity-item:last-child, .issue-item:last-child {
                    border-bottom: none;
                }

                .activity-title, .issue-title {
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 4px;
                }

                .activity-meta, .issue-meta {
                    font-size: 0.9rem;
                    color: #6b7280;
                }

                .activity-status, .issue-status {
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    font-weight: 600;
                }

                .status-backlog { background: #fef3c7; color: #92400e; }
                .status-design { background: #ddd6fe; color: #6d28d9; }
                .status-planning { background: #bfdbfe; color: #1d4ed8; }

                .info-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 16px;
                }

                .info-item {
                    background: white;
                    padding: 16px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    font-size: 0.9rem;
                    line-height: 1.5;
                }

                .loading-container, .error-container {
                    text-align: center;
                    padding: 60px 20px;
                }

                .loading-spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f4f6;
                    border-top: 4px solid #3b82f6;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                @media (max-width: 768px) {
                    .enhanced-dashboard {
                        padding: 16px;
                    }
                    
                    .dashboard-header h1 {
                        font-size: 2rem;
                    }
                    
                    .stats-grid {
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 16px;
                    }
                    
                    .enhanced-projects-grid {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        `;
    }

    renderEnhancedProjectCard(project) {
        const formattedProject = this.dataManager.formatProjectForDisplay(project.id);
        
        return `
            <div class="enhanced-project-card">
                <div class="project-header">
                    <div class="project-title">${project.title}</div>
                    <div class="project-field">${project.field}</div>
                </div>
                <div class="project-body">
                    <div class="project-description">${project.description}</div>
                    <div class="project-meta">
                        <div class="meta-item">
                            <div class="meta-label">Completeness</div>
                            <div class="meta-value">${project.completeness}%</div>
                            <div class="completeness-bar">
                                <div class="completeness-fill" style="width: ${project.completeness}%"></div>
                            </div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Modified</div>
                            <div class="meta-value">${formattedProject.formattedModified}</div>
                        </div>
                    </div>
                    <div class="enhancement-badge">
                        🤖 Enhanced by ${project.contributors.find(c => c.name === 'Google Gemini')?.role || 'Gemini'}
                    </div>
                </div>
            </div>
        `;
    }

    renderFieldCard(field, count) {
        return `
            <div class="field-card">
                <div class="field-name">${field}</div>
                <div class="field-count">${count}</div>
            </div>
        `;
    }

    renderActivityItem(project) {
        return `
            <div class="activity-item">
                <div>
                    <div class="activity-title">${project.title}</div>
                    <div class="activity-meta">
                        Modified: ${new Date(project.dateModified).toLocaleDateString()} • 
                        ${project.completeness}% complete
                    </div>
                </div>
                <div class="activity-status status-${project.status}">${project.status}</div>
            </div>
        `;
    }

    renderIssueItem(project) {
        return `
            <div class="issue-item">
                <div>
                    <div class="issue-title">${project.title}</div>
                    <div class="issue-meta">
                        Issues: ${project.issues.join(', ')}
                    </div>
                </div>
                <div class="issue-status status-${project.status}">${project.completeness}%</div>
            </div>
        `;
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboard-container')) {
        new EnhancedDashboard('dashboard-container');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedDashboard;
}

console.log('📊 EnhancedDashboard component loaded');