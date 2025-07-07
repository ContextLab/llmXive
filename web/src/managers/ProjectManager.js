/**
 * ProjectManager - Manages project lifecycle and metadata
 * 
 * Handles project creation, reading, updating, and status management
 * for the llmXive system.
 */

class ProjectManager {
    constructor(fileManager, systemConfig) {
        this.fileManager = fileManager;
        this.systemConfig = systemConfig;
        this.projectsPath = '.llmxive-system/registry/projects.json';
        this.projectTemplates = new Map();
        
        this.initializeTemplates();
    }
    
    /**
     * Initialize project templates
     */
    initializeTemplates() {
        // Standard research project template
        this.projectTemplates.set('research', {
            type: 'research',
            phases: ['idea', 'design', 'implementation_plan', 'implementation', 'paper', 'review'],
            requiredArtifacts: {
                idea: ['initial-idea.md'],
                design: ['technical-design/main.md'],
                implementation_plan: ['implementation-plan/main.md'],
                implementation: ['code/src/', 'data/processed/'],
                paper: ['paper/main.tex', 'paper/bibliography.bib'],
                review: ['reviews/final/']
            },
            estimatedDuration: {
                idea: 3,
                design: 7,
                implementation_plan: 5,
                implementation: 21,
                paper: 14,
                review: 7
            }
        });
        
        // Analysis-only project template
        this.projectTemplates.set('analysis', {
            type: 'analysis',
            phases: ['idea', 'design', 'implementation', 'review'],
            requiredArtifacts: {
                idea: ['initial-idea.md'],
                design: ['technical-design/main.md'],
                implementation: ['code/notebooks/', 'data/processed/'],
                review: ['reviews/final/']
            },
            estimatedDuration: {
                idea: 2,
                design: 5,
                implementation: 14,
                review: 5
            }
        });
    }
    
    /**
     * Create a new project
     */
    async createProject(projectData) {
        try {
            // Validate project data
            await this.validateProjectData(projectData);
            
            // Generate unique project ID
            const projectId = await this.generateProjectId(projectData.title);
            
            // Get project template
            const template = this.projectTemplates.get(projectData.type || 'research');
            if (!template) {
                throw new Error(`Unknown project type: ${projectData.type}`);
            }
            
            // Create project directory structure
            await this.createProjectStructure(projectId, template);
            
            // Create project configuration
            const projectConfig = await this.createProjectConfig(projectId, projectData, template);
            
            // Register project in system
            await this.registerProject(projectId, projectConfig);
            
            // Create initial artifacts
            await this.createInitialArtifacts(projectId, projectData);
            
            // Log project creation
            await this.fileManager.appendToLog('.llmxive-system/logs/projects.json', {
                type: 'project_created',
                projectId: projectId,
                title: projectData.title,
                creator: projectData.creator || 'unknown',
                template: template.type
            });
            
            console.log(`Project created successfully: ${projectId}`);
            return {
                projectId,
                status: 'created',
                config: projectConfig
            };
            
        } catch (error) {
            console.error('Failed to create project:', error);
            throw error;
        }
    }
    
    /**
     * Validate project data
     */
    async validateProjectData(projectData) {
        const requiredFields = ['title', 'description'];
        
        for (const field of requiredFields) {
            if (!projectData[field]) {
                throw new Error(`Missing required field: ${field}`);
            }
        }
        
        // Validate title format
        if (projectData.title.length < 5 || projectData.title.length > 100) {
            throw new Error('Project title must be between 5 and 100 characters');
        }
        
        // Check for duplicate titles
        const existingProjects = await this.listProjects();
        const titleExists = existingProjects.some(p => 
            p.title.toLowerCase() === projectData.title.toLowerCase()
        );
        
        if (titleExists) {
            throw new Error('A project with this title already exists');
        }
        
        return true;
    }
    
    /**
     * Generate unique project ID
     */
    async generateProjectId(title) {
        // Convert title to slug format
        const baseSlug = title
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/--+/g, '-')
            .trim('-')
            .substring(0, 50);
        
        // Get current date for ID prefix
        const date = new Date();
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        
        // Generate base ID
        let projectId = `PROJ-${year}${month}${day}-${baseSlug}`;
        
        // Ensure uniqueness
        let counter = 1;
        while (await this.projectExists(projectId)) {
            projectId = `PROJ-${year}${month}${day}-${baseSlug}-${counter}`;
            counter++;
        }
        
        return projectId;
    }
    
    /**
     * Check if project exists
     */
    async projectExists(projectId) {
        try {
            const config = await this.fileManager.readJSON(`projects/${projectId}/.llmxive/config.json`);
            return !!config;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Create project directory structure
     */
    async createProjectStructure(projectId, template) {
        const projectPath = `projects/${projectId}`;
        
        // Core project directories
        const directories = [
            `${projectPath}`,
            `${projectPath}/.llmxive`,
            `${projectPath}/idea`,
            `${projectPath}/technical-design`,
            `${projectPath}/technical-design/diagrams`,
            `${projectPath}/technical-design/specifications`,
            `${projectPath}/implementation-plan`,
            `${projectPath}/implementation-plan/milestones`,
            `${projectPath}/implementation-plan/tasks`,
            `${projectPath}/code`,
            `${projectPath}/code/src`,
            `${projectPath}/code/tests`,
            `${projectPath}/code/notebooks`,
            `${projectPath}/code/scripts`,
            `${projectPath}/code/experiments`,
            `${projectPath}/data`,
            `${projectPath}/data/raw`,
            `${projectPath}/data/processed`,
            `${projectPath}/data/synthetic`,
            `${projectPath}/data/external`,
            `${projectPath}/reviews`,
            `${projectPath}/reviews/automated`,
            `${projectPath}/reviews/manual`
        ];
        
        // Add template-specific directories
        if (template.phases.includes('paper')) {
            directories.push(
                `${projectPath}/paper`,
                `${projectPath}/paper/sections`,
                `${projectPath}/paper/figures`,
                `${projectPath}/paper/tables`,
                `${projectPath}/paper/supplements`,
                `${projectPath}/paper/drafts`
            );
        }
        
        // Create all directories
        for (const dir of directories) {
            await this.fileManager.createDirectory(dir);
        }
    }
    
    /**
     * Create project configuration
     */
    async createProjectConfig(projectId, projectData, template) {
        const config = {
            project: {
                id: projectId,
                title: projectData.title,
                description: projectData.description,
                type: template.type,
                status: 'active',
                priority: projectData.priority || 'medium',
                created_date: new Date().toISOString(),
                last_updated: new Date().toISOString(),
                estimated_completion: this.calculateEstimatedCompletion(template)
            },
            template: {
                type: template.type,
                version: '1.0',
                phases: template.phases
            },
            contributors: [{
                name: projectData.creator || 'anonymous',
                role: 'creator',
                type: projectData.creatorType || 'human',
                contributions: ['creation'],
                joined_date: new Date().toISOString()
            }],
            phases: this.initializePhases(template),
            dependencies: {
                internal: [],
                external: []
            },
            metrics: {
                total_reviews: 0,
                total_points: 0,
                phase_completion: 0,
                quality_score: 0
            }
        };
        
        // Write project configuration
        await this.fileManager.writeJSON(
            `projects/${projectId}/.llmxive/config.json`,
            config,
            `Initialize project configuration for ${projectId}`
        );
        
        return config;
    }
    
    /**
     * Initialize phase tracking
     */
    initializePhases(template) {
        const phases = {};
        
        template.phases.forEach((phase, index) => {
            phases[phase] = {
                id: phase,
                name: this.getPhaseDisplayName(phase),
                status: index === 0 ? 'in_progress' : 'pending',
                artifacts: [],
                reviews: {
                    automated: [],
                    manual: [],
                    total_points: 0,
                    required_points: this.getRequiredPoints(phase)
                },
                started_date: index === 0 ? new Date().toISOString() : null,
                completed_date: null,
                estimated_duration_days: template.estimatedDuration[phase] || 7
            };
        });
        
        return phases;
    }
    
    /**
     * Get phase display name
     */
    getPhaseDisplayName(phase) {
        const names = {
            idea: 'Project Ideation',
            design: 'Technical Design',
            implementation_plan: 'Implementation Planning',
            implementation: 'Implementation',
            paper: 'Paper Writing',
            review: 'Final Review'
        };
        
        return names[phase] || phase;
    }
    
    /**
     * Get required review points for phase
     */
    getRequiredPoints(phase) {
        const points = {
            idea: 2.0,
            design: 3.0,
            implementation_plan: 3.0,
            implementation: 5.0,
            paper: 7.0,
            review: 10.0
        };
        
        return points[phase] || 3.0;
    }
    
    /**
     * Calculate estimated completion date
     */
    calculateEstimatedCompletion(template) {
        const totalDays = Object.values(template.estimatedDuration).reduce((sum, days) => sum + days, 0);
        const completionDate = new Date();
        completionDate.setDate(completionDate.getDate() + totalDays);
        return completionDate.toISOString();
    }
    
    /**
     * Register project in system registry
     */
    async registerProject(projectId, config) {
        const registry = await this.fileManager.readJSON(this.projectsPath) || {
            version: '1.0',
            created: new Date().toISOString(),
            projects: {},
            statistics: { by_status: {}, by_type: {} }
        };
        
        // Add project to registry
        registry.projects[projectId] = {
            id: projectId,
            title: config.project.title,
            type: config.project.type,
            status: config.project.status,
            created_date: config.project.created_date,
            last_updated: config.project.last_updated,
            current_phase: this.getCurrentPhase(config.phases),
            completion_percentage: 0
        };
        
        // Update statistics
        registry.total_projects = Object.keys(registry.projects).length;
        registry.last_updated = new Date().toISOString();
        
        // Update status statistics
        const statusStats = {};
        const typeStats = {};
        
        Object.values(registry.projects).forEach(project => {
            statusStats[project.status] = (statusStats[project.status] || 0) + 1;
            typeStats[project.type] = (typeStats[project.type] || 0) + 1;
        });
        
        registry.statistics.by_status = statusStats;
        registry.statistics.by_type = typeStats;
        
        // Write updated registry
        await this.fileManager.writeJSON(
            this.projectsPath,
            registry,
            `Register new project: ${projectId}`
        );
    }
    
    /**
     * Get current phase of project
     */
    getCurrentPhase(phases) {
        // Find the first phase that's not completed
        for (const [phaseId, phase] of Object.entries(phases)) {
            if (phase.status !== 'completed') {
                return phaseId;
            }
        }
        
        // All phases completed
        return 'completed';
    }
    
    /**
     * Create initial artifacts
     */
    async createInitialArtifacts(projectId, projectData) {
        const projectPath = `projects/${projectId}`;
        
        // Create initial idea document
        const ideaContent = `# ${projectData.title}

## Project Overview

${projectData.description}

## Research Questions

1. [Add your research questions here]
2. [Add more as needed]

## Motivation

[Explain why this project is important and what gaps it addresses]

## Expected Outcomes

[Describe what you expect to achieve with this project]

## Initial Thoughts

[Add any initial thoughts, hypotheses, or approaches]

---

*Project created: ${new Date().toISOString()}*
*Creator: ${projectData.creator || 'Anonymous'}*
`;
        
        await this.fileManager.writeJSON(
            `${projectPath}/idea/initial-idea.md`,
            ideaContent,
            `Create initial idea document for ${projectId}`,
            true // Allow creation of new file
        );
        
        // Create README for the project
        const readmeContent = `# ${projectData.title}

**Project ID**: ${projectId}  
**Type**: ${projectData.type || 'research'}  
**Status**: Active  
**Created**: ${new Date().toDateString()}

## Description

${projectData.description}

## Project Structure

- **\`idea/\`**: Initial project concept and brainstorming
- **\`technical-design/\`**: Technical design documents and specifications  
- **\`implementation-plan/\`**: Implementation planning and milestones
- **\`code/\`**: Source code, tests, and analysis notebooks
- **\`data/\`**: Raw and processed datasets
- **\`paper/\`**: LaTeX manuscript and figures (if applicable)
- **\`reviews/\`**: Peer reviews and feedback

## Current Phase

🟡 **Ideation** - Developing and refining the project concept

## Contributors

- ${projectData.creator || 'Anonymous'} (Creator)

## Getting Started

1. Review the initial idea in \`idea/initial-idea.md\`
2. Contribute to the brainstorming process
3. Help advance the project through review and feedback

---

*This project is part of the llmXive automated research platform.*
`;
        
        await this.fileManager.writeJSON(
            `${projectPath}/README.md`,
            readmeContent,
            `Create README for ${projectId}`,
            true
        );
    }
    
    /**
     * Get project configuration
     */
    async getProject(projectId) {
        try {
            const config = await this.fileManager.readJSON(`projects/${projectId}/.llmxive/config.json`);
            return config;
        } catch (error) {
            console.error(`Failed to get project ${projectId}:`, error);
            return null;
        }
    }
    
    /**
     * Update project configuration
     */
    async updateProject(projectId, updates) {
        try {
            const config = await this.getProject(projectId);
            if (!config) {
                throw new Error(`Project not found: ${projectId}`);
            }
            
            // Merge updates
            const updatedConfig = {
                ...config,
                ...updates,
                project: {
                    ...config.project,
                    ...updates.project,
                    last_updated: new Date().toISOString()
                }
            };
            
            // Write updated configuration
            await this.fileManager.writeJSON(
                `projects/${projectId}/.llmxive/config.json`,
                updatedConfig,
                `Update project configuration for ${projectId}`
            );
            
            // Update registry
            await this.updateProjectInRegistry(projectId, updatedConfig);
            
            return updatedConfig;
            
        } catch (error) {
            console.error(`Failed to update project ${projectId}:`, error);
            throw error;
        }
    }
    
    /**
     * Update project in registry
     */
    async updateProjectInRegistry(projectId, config) {
        const registry = await this.fileManager.readJSON(this.projectsPath);
        
        if (registry && registry.projects[projectId]) {
            registry.projects[projectId] = {
                ...registry.projects[projectId],
                title: config.project.title,
                status: config.project.status,
                last_updated: config.project.last_updated,
                current_phase: this.getCurrentPhase(config.phases),
                completion_percentage: this.calculateCompletionPercentage(config.phases)
            };
            
            registry.last_updated = new Date().toISOString();
            
            await this.fileManager.writeJSON(
                this.projectsPath,
                registry,
                `Update project registry for ${projectId}`
            );
        }
    }
    
    /**
     * Calculate completion percentage
     */
    calculateCompletionPercentage(phases) {
        const phaseArray = Object.values(phases);
        const completedPhases = phaseArray.filter(phase => phase.status === 'completed').length;
        return Math.round((completedPhases / phaseArray.length) * 100);
    }
    
    /**
     * List all projects
     */
    async listProjects() {
        try {
            const registry = await this.fileManager.readJSON(this.projectsPath);
            return registry ? Object.values(registry.projects) : [];
        } catch (error) {
            console.error('Failed to list projects:', error);
            return [];
        }
    }
    
    /**
     * Get project statistics
     */
    async getProjectStatistics() {
        try {
            const registry = await this.fileManager.readJSON(this.projectsPath);
            return registry ? registry.statistics : null;
        } catch (error) {
            console.error('Failed to get project statistics:', error);
            return null;
        }
    }
}

export default ProjectManager;