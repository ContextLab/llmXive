/**
 * Project Data Manager for llmXive Web Interface
 * 
 * Manages loading and accessing project data from the local database
 */

class ProjectDataManager {
    constructor() {
        this.projects = null;
        this.contributors = null;
        this.analytics = null;
        this.loaded = false;
    }

    /**
     * Load all database files
     */
    async loadData() {
        try {
            console.log('📚 Loading llmXive project data...');
            
            // Load all database files in parallel
            const [projectsResponse, contributorsResponse, analyticsResponse] = await Promise.all([
                fetch('database/projects.json'),
                fetch('database/contributors.json'),
                fetch('database/analytics.json')
            ]);

            if (!projectsResponse.ok || !contributorsResponse.ok || !analyticsResponse.ok) {
                throw new Error('Failed to load one or more database files');
            }

            const [projectsData, contributorsData, analyticsData] = await Promise.all([
                projectsResponse.json(),
                contributorsResponse.json(),
                analyticsResponse.json()
            ]);

            this.projects = projectsData;
            this.contributors = contributorsData;
            this.analytics = analyticsData;
            this.loaded = true;

            // Load any additional projects from localStorage
            this.loadFromLocalStorage();

            console.log('✅ Project data loaded successfully');
            console.log(`📊 Loaded ${this.getProjectCount()} projects`);
            console.log(`👥 ${Object.keys(this.contributors.contributors).length} contributors`);
            console.log(`📈 Average completeness: ${this.analytics.stats.totalCompleteness}%`);

            return true;
        } catch (error) {
            console.error('❌ Failed to load project data:', error);
            console.log('🔄 Loading fallback embedded data...');
            
            // Load embedded fallback data when fetch fails (CORS issues)
            this.loadEmbeddedData();
            return true;
        }
    }

    /**
     * Load embedded fallback data for CORS issues
     */
    loadEmbeddedData() {
        // Embedded projects data
        this.projects = {
            "metadata": {
                "version": "1.0.0",
                "created": "2025-07-07",
                "description": "llmXive Projects Database with corrected dates and attributions",
                "totalProjects": 3,
                "dateRange": "2025-07-01 to 2025-07-07"
            },
            "projects": {
                "llmxive-auto-001": {
                    "id": "llmxive-auto-001",
                    "title": "llmXive Automation System",
                    "description": "Fully automated research pipeline using GitHub Actions and HuggingFace models",
                    "field": "Infrastructure/Meta-project",
                    "status": "backlog",
                    "phase": "design",
                    "githubIssue": 21,
                    "dateCreated": "2025-07-04",
                    "dateModified": "2025-07-04",
                    "contributors": [
                        {
                            "type": "AI",
                            "name": "Claude",
                            "model": "Claude 4 Sonnet",
                            "role": "primary_author",
                            "dateContributed": "2025-07-04"
                        }
                    ],
                    "completeness": 15,
                    "keywords": ["automation", "github-actions", "huggingface", "pipeline"],
                    "dependencies": ["GitHub Actions", "HuggingFace API", "Docker"],
                    "location": "technical_design_documents/llmXive_automation/design.md",
                    "estimatedTimeline": "2025-07-01 to 2026-01-01"
                },
                "llmxive-v2-final": {
                    "id": "llmxive-v2-final", 
                    "title": "llmXive v2.0 System Architecture",
                    "description": "Next-generation llmXive system with LaTeX template integration",
                    "field": "Architecture/Meta-project",
                    "status": "design",
                    "phase": "design",
                    "githubIssue": null,
                    "dateCreated": "2025-07-04",
                    "dateModified": "2025-07-07",
                    "contributors": [
                        {
                            "type": "AI",
                            "name": "Claude",
                            "model": "Claude 4 Sonnet",
                            "role": "primary_author",
                            "dateContributed": "2025-07-04"
                        },
                        {
                            "type": "human",
                            "name": "Jeremy Manning",
                            "role": "contributor",
                            "dateContributed": "2025-07-05"
                        }
                    ],
                    "completeness": 30,
                    "keywords": ["architecture", "latex", "github-native", "v2.0"],
                    "dependencies": ["GitHub Pages", "Docker", "LaTeX"],
                    "location": "technical_design_documents/llmxive-v2-final/design.md",
                    "estimatedTimeline": "2025-07-01 to 2025-09-01"
                },
                "biology-example": {
                    "id": "biology-example",
                    "title": "Exploring Gene Regulation Mechanisms",
                    "description": "Multi-scale approach to understanding gene regulation mechanisms across different cell types",
                    "field": "Biology",
                    "status": "backlog",
                    "phase": "idea",
                    "githubIssue": 30,
                    "dateCreated": "2025-07-01",
                    "dateModified": "2025-07-07",
                    "contributors": [
                        {
                            "type": "AI",
                            "name": "Claude",
                            "model": "Claude 4 Sonnet",
                            "role": "primary_author",
                            "dateContributed": "2025-07-01"
                        }
                    ],
                    "completeness": 20,
                    "keywords": ["gene-regulation", "cell-types", "genomics", "bioinformatics"],
                    "dependencies": ["Bioinformatics tools", "Laboratory equipment"],
                    "location": "technical_design_documents/biology-example/design.md",
                    "estimatedTimeline": "2025-07-01 to 2028-07-01",
                    "reviews": [
                        {
                            "date": "2025-07-07",
                            "type": "design",
                            "score": 0.75,
                            "result": "revision_needed",
                            "reviewer": "Gemini"
                        }
                    ]
                }
            }
        };

        // Embedded contributors data
        this.contributors = {
            "metadata": {
                "version": "1.0.0",
                "created": "2025-07-07",
                "totalContributors": 4
            },
            "contributors": {
                "claude": {
                    "name": "Claude",
                    "type": "AI",
                    "model": "Claude 4 Sonnet",
                    "organization": "Anthropic",
                    "specialties": ["Technical writing", "Code development", "Research design"],
                    "totalProjects": 3,
                    "primaryProjects": 2
                },
                "jeremy-manning": {
                    "name": "Jeremy Manning",
                    "type": "human",
                    "organization": "Dartmouth College",
                    "specialties": ["Computational neuroscience", "Data science", "Machine learning"],
                    "totalProjects": 1,
                    "primaryProjects": 0
                },
                "gemini": {
                    "name": "Gemini",
                    "type": "AI", 
                    "model": "Google Gemini",
                    "organization": "Google",
                    "specialties": ["Code review", "Content enhancement"],
                    "totalProjects": 1,
                    "primaryProjects": 0
                }
            }
        };

        // Embedded analytics data
        this.analytics = {
            "metadata": {
                "version": "1.0.0",
                "created": "2025-07-07",
                "calculatedFrom": "embedded-projects"
            },
            "stats": {
                "totalProjects": 3,
                "totalCompleteness": 22,
                "uniqueAuthors": 3,
                "uniqueFields": 2
            },
            "projectsByField": {
                "Infrastructure/Meta-project": 2,
                "Biology": 1
            },
            "projectsByStatus": {
                "backlog": 2,
                "design": 1
            }
        };

        this.loaded = true;
        console.log('✅ Embedded data loaded successfully');
        console.log(`📊 Loaded ${this.getProjectCount()} projects (embedded)`);
    }

    /**
     * Get all projects with calculated completeness
     */
    getAllProjects() {
        this.ensureLoaded();
        const projects = {};
        for (const [id, project] of Object.entries(this.projects.projects)) {
            projects[id] = {
                ...project,
                completeness: this.calculateCompleteness(project)
            };
        }
        return projects;
    }

    /**
     * Get project by ID with calculated completeness
     */
    getProject(projectId) {
        this.ensureLoaded();
        const project = this.projects.projects[projectId];
        if (!project) return null;
        
        return {
            ...project,
            completeness: this.calculateCompleteness(project)
        };
    }

    /**
     * Get projects by field
     */
    getProjectsByField(field) {
        this.ensureLoaded();
        return Object.values(this.projects.projects).filter(project => 
            project.field.toLowerCase().includes(field.toLowerCase())
        );
    }

    /**
     * Get projects by status
     */
    getProjectsByStatus(status) {
        this.ensureLoaded();
        return Object.values(this.projects.projects).filter(project => 
            project.status === status
        );
    }


    /**
     * Get projects by completeness range (using calculated completeness)
     */
    getProjectsByCompleteness(minPercent, maxPercent) {
        this.ensureLoaded();
        return Object.values(this.projects.projects).filter(project => {
            const completeness = this.calculateCompleteness(project);
            return completeness >= minPercent && completeness <= maxPercent;
        }).map(project => ({
            ...project,
            completeness: this.calculateCompleteness(project)
        }));
    }

    /**
     * Get contributor information
     */
    getContributor(contributorKey) {
        this.ensureLoaded();
        return this.contributors.contributors[contributorKey];
    }

    /**
     * Get all contributors
     */
    getAllContributors() {
        this.ensureLoaded();
        return this.contributors.contributors;
    }

    /**
     * Calculate project completeness based on stages and artifacts
     */
    calculateCompleteness(project) {
        let completeness = 0;
        
        // Stage 1: Idea generation (1%)
        if (project.id && project.title && project.description) {
            completeness += 1;
        }
        
        // Stage 2: Technical design (5%)
        if (project.phase === 'design' || this.hasLaterPhase(project.phase)) {
            completeness += 5;
        }
        
        // Stage 3: Tech design reviews (up to 5%)
        const designReviews = this.getProjectReviews(project, 'design');
        completeness += Math.min(5, this.calculateReviewScore(designReviews));
        
        // Stage 4: Implementation plan (5%)
        if (project.phase === 'implementation_plan' || this.hasLaterPhase(project.phase)) {
            completeness += 5;
        }
        
        // Stage 5: Implementation plan reviews (up to 5%)
        const implReviews = this.getProjectReviews(project, 'implementation');
        completeness += Math.min(5, this.calculateReviewScore(implReviews));
        
        // Stage 6: Code/Data/Paper (40% total)
        const artifacts = this.getProjectArtifacts(project);
        if (artifacts.hasCode) completeness += 10;
        if (artifacts.hasData) completeness += 10;
        if (artifacts.hasPaper) {
            // Paper gets 20% normally, or up to 40% if code/data missing
            const paperBonus = 20 + (artifacts.hasCode ? 0 : 10) + (artifacts.hasData ? 0 : 10);
            completeness += paperBonus;
        }
        
        // Stage 7: Final reviews (up to 5%)
        const finalReviews = this.getProjectReviews(project, 'final');
        completeness += Math.min(5, this.calculateReviewScore(finalReviews));
        
        // Stage 8: Final verification (29%)
        if (this.isFullyVerified(project)) {
            completeness += 29;
        }
        
        return Math.min(100, Math.round(completeness));
    }
    
    /**
     * Check if project phase is later than given phase
     */
    hasLaterPhase(currentPhase) {
        const phases = ['backlog', 'design', 'implementation_plan', 'in_progress', 'review', 'done'];
        const phaseIndex = phases.indexOf(currentPhase);
        return phaseIndex > 1; // Later than 'design'
    }
    
    /**
     * Get reviews for a project by type
     */
    getProjectReviews(project, reviewType) {
        return (project.reviews || []).filter(review => 
            review.type === reviewType || 
            (reviewType === 'design' && !review.type) // Default to design reviews
        );
    }
    
    /**
     * Calculate review score based on reviewer types
     */
    calculateReviewScore(reviews) {
        let score = 0;
        for (const review of reviews) {
            if (review.reviewer === 'human' || review.reviewer?.includes('Manning')) {
                score += 1; // Human review = 1%
            } else {
                score += 0.5; // LLM review = 0.5%
            }
        }
        return score;
    }
    
    /**
     * Check what artifacts exist for a project
     */
    getProjectArtifacts(project) {
        // This is a simplified check - in a real system, you'd check file existence
        return {
            hasCode: project.location?.includes('code/') || project.keywords?.includes('code'),
            hasData: project.keywords?.includes('data') || project.field?.includes('Data'),
            hasPaper: project.location?.includes('papers/') || project.phase === 'done'
        };
    }
    
    /**
     * Check if project is fully verified
     */
    isFullyVerified(project) {
        // This would check that all references are validated, code runs, etc.
        return project.status === 'done' && project.verified === true;
    }

    /**
     * Get analytics data
     */
    getAnalytics() {
        this.ensureLoaded();
        return this.analytics.stats;
    }

    /**
     * Search projects by keyword
     */
    searchProjects(query) {
        this.ensureLoaded();
        const lowercaseQuery = query.toLowerCase();
        
        return Object.values(this.projects.projects).filter(project => {
            return (
                project.title.toLowerCase().includes(lowercaseQuery) ||
                project.description.toLowerCase().includes(lowercaseQuery) ||
                project.keywords.some(keyword => keyword.toLowerCase().includes(lowercaseQuery)) ||
                project.field.toLowerCase().includes(lowercaseQuery)
            );
        });
    }

    /**
     * Get project statistics
     */
    getProjectCount() {
        this.ensureLoaded();
        return Object.keys(this.projects.projects).length;
    }

    /**
     * Get projects with issues
     */
    getProjectsWithIssues() {
        this.ensureLoaded();
        return Object.values(this.projects.projects).filter(project =>
            project.issues && project.issues.length > 0
        );
    }

    /**
     * Get recent projects (within last week) with calculated completeness
     */
    getRecentProjects() {
        this.ensureLoaded();
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        
        return Object.values(this.projects.projects).filter(project => {
            const modifiedDate = new Date(project.dateModified);
            return modifiedDate >= oneWeekAgo;
        }).map(project => ({
            ...project,
            completeness: this.calculateCompleteness(project)
        }));
    }

    /**
     * Get project timeline info
     */
    getProjectTimeline(projectId) {
        const project = this.getProject(projectId);
        if (!project) return null;

        return {
            created: project.dateCreated,
            modified: project.dateModified,
            estimatedTimeline: project.estimatedTimeline,
            contributors: project.contributors.map(c => ({
                name: c.name,
                role: c.role,
                dateContributed: c.dateContributed
            }))
        };
    }

    /**
     * Format project for display
     */
    formatProjectForDisplay(projectId) {
        const project = this.getProject(projectId);
        if (!project) return null;

        return {
            ...project,
            formattedCreated: new Date(project.dateCreated).toLocaleDateString(),
            formattedModified: new Date(project.dateModified).toLocaleDateString(),
            contributorNames: project.contributors.map(c => c.name).join(', '),
            completenessLabel: this.getCompletenessLabel(project.completeness),
            hasIssues: project.issues && project.issues.length > 0
        };
    }

    /**
     * Get completeness label
     */
    getCompletenessLabel(completeness) {
        if (completeness >= 90) return 'Excellent';
        if (completeness >= 80) return 'Good';
        if (completeness >= 60) return 'Fair';
        if (completeness >= 40) return 'Developing';
        return 'Needs Work';
    }

    /**
     * Ensure data is loaded
     */
    ensureLoaded() {
        if (!this.loaded) {
            throw new Error('Project data not loaded. Call loadData() first.');
        }
    }

    /**
     * Get summary statistics for dashboard
     */
    getDashboardStats() {
        this.ensureLoaded();
        
        const projects = Object.values(this.projects.projects);
        
        // Count unique authors across all projects
        const allAuthors = new Set();
        projects.forEach(project => {
            project.contributors.forEach(contributor => {
                allAuthors.add(contributor.name);
            });
        });
        
        const issuesCount = projects.filter(p => 
            p.issues && p.issues.length > 0
        ).length;

        const avgCompleteness = Math.round(
            projects.reduce((sum, p) => sum + this.calculateCompleteness(p), 0) / projects.length
        );

        return {
            totalProjects: projects.length,
            uniqueAuthors: allAuthors.size,
            projectsWithIssues: issuesCount,
            averageCompleteness: avgCompleteness,
            recentProjects: this.getRecentProjects().length,
            dateRange: this.analytics.stats.dateRange,
            fieldDistribution: this.analytics.stats.projectsByField,
            statusDistribution: this.analytics.stats.projectsByStatus
        };
    }

    /**
     * Update an existing project with new data
     */
    async updateProject(projectId, updates) {
        this.ensureLoaded();
        
        if (!this.projects.projects[projectId]) {
            throw new Error(`Project with ID '${projectId}' not found`);
        }

        try {
            // Update project data
            this.projects.projects[projectId] = {
                ...this.projects.projects[projectId],
                ...updates,
                dateModified: new Date().toISOString().split('T')[0]
            };
            
            // Save to localStorage
            this.saveToLocalStorage();
            
            console.log(`✅ Updated project: ${projectId}`);
            return this.projects.projects[projectId];
        } catch (error) {
            console.error('Failed to update project:', error);
            throw error;
        }
    }

    /**
     * Add a new project to the database with persistent storage
     */
    async addProject(newProject) {
        this.ensureLoaded();
        
        // Validate required fields
        if (!newProject.id || !newProject.title || !newProject.description || !newProject.field) {
            throw new Error('Missing required project fields');
        }

        // Check if project already exists
        if (this.projects.projects[newProject.id]) {
            throw new Error(`Project with ID '${newProject.id}' already exists`);
        }

        try {
            // Use DatabaseManager for atomic operation if available
            if (window.DatabaseManager) {
                await window.DatabaseManager.addProject(newProject);
                
                // Update local copy
                this.projects.projects[newProject.id] = newProject;
                this.projects.metadata.totalProjects = Object.keys(this.projects.projects).length;
                this.projects.metadata.dateRange = this.calculateDateRange();
            } else {
                // Fallback to localStorage
                this.projects.projects[newProject.id] = newProject;
                this.projects.metadata.totalProjects = Object.keys(this.projects.projects).length;
                this.projects.metadata.dateRange = this.calculateDateRange();
                this.saveToLocalStorage();
            }
            
            console.log(`✅ Added new project: ${newProject.title}`);
            return newProject;
        } catch (error) {
            console.error('Failed to add project:', error);
            throw error;
        }
    }

    /**
     * Calculate date range for metadata
     */
    calculateDateRange() {
        const projects = Object.values(this.projects.projects);
        if (projects.length === 0) return '';

        const dates = projects.map(p => new Date(p.dateCreated)).sort();
        const earliest = dates[0].toISOString().split('T')[0];
        const latest = dates[dates.length - 1].toISOString().split('T')[0];
        
        return `${earliest} to ${latest}`;
    }

    /**
     * Save data to localStorage for persistence
     */
    saveToLocalStorage() {
        try {
            localStorage.setItem('llmxive-projects', JSON.stringify(this.projects));
            console.log('💾 Projects saved to localStorage');
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
        }
    }

    /**
     * Load data from localStorage if available
     */
    loadFromLocalStorage() {
        try {
            const stored = localStorage.getItem('llmxive-projects');
            if (stored) {
                const storedData = JSON.parse(stored);
                // Safely merge with existing data, prioritizing localStorage
                if (storedData && storedData.projects && typeof storedData.projects === 'object') {
                    Object.assign(this.projects.projects, storedData.projects);
                    console.log('📂 Loaded projects from localStorage');
                    return true;
                }
            }
        } catch (error) {
            console.error('Failed to load from localStorage:', error);
            // Clear corrupted localStorage
            localStorage.removeItem('llmxive-projects');
        }
        return false;
    }
}

// Create global instance
window.ProjectDataManager = window.ProjectDataManager || new ProjectDataManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProjectDataManager;
}

console.log('📦 ProjectDataManager loaded');