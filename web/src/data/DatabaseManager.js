/**
 * Database Manager for llmXive
 * Handles persistent storage with concurrency control and atomic operations
 */

class DatabaseManager {
    constructor() {
        this.lockfile = 'database/.lock';
        this.maxRetries = 5;
        this.retryDelay = 100; // ms
    }

    /**
     * Acquire a lock for database operations
     */
    async acquireLock() {
        for (let i = 0; i < this.maxRetries; i++) {
            try {
                // Check if lock file exists
                const lockExists = await this.checkLockExists();
                if (!lockExists) {
                    // Create lock file with timestamp
                    await this.createLockFile();
                    return true;
                }
                
                // Wait and retry
                await this.sleep(this.retryDelay * (i + 1));
            } catch (error) {
                console.error('Lock acquisition error:', error);
            }
        }
        throw new Error('Failed to acquire database lock after ' + this.maxRetries + ' attempts');
    }

    /**
     * Release the database lock
     */
    async releaseLock() {
        try {
            await fetch('database/.lock', { method: 'DELETE' });
        } catch (error) {
            console.warn('Failed to release lock:', error);
        }
    }

    /**
     * Check if lock file exists
     */
    async checkLockExists() {
        try {
            const response = await fetch('database/.lock');
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    /**
     * Create lock file
     */
    async createLockFile() {
        const lockData = {
            timestamp: Date.now(),
            session: Math.random().toString(36)
        };
        
        const response = await fetch('database/.lock', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lockData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create lock file');
        }
    }

    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Atomic read operation
     */
    async atomicRead(filename) {
        await this.acquireLock();
        try {
            const response = await fetch(`database/${filename}`);
            if (!response.ok) {
                throw new Error(`Failed to read ${filename}`);
            }
            const data = await response.json();
            return data;
        } finally {
            await this.releaseLock();
        }
    }

    /**
     * Atomic write operation with backup
     */
    async atomicWrite(filename, data) {
        await this.acquireLock();
        try {
            // Create backup first
            await this.createBackup(filename);
            
            // Write new data
            const response = await fetch(`database/${filename}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data, null, 2)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to write ${filename}`);
            }
            
            return true;
        } catch (error) {
            // Restore from backup on error
            await this.restoreBackup(filename);
            throw error;
        } finally {
            await this.releaseLock();
        }
    }

    /**
     * Create backup of file
     */
    async createBackup(filename) {
        try {
            const response = await fetch(`database/${filename}`);
            if (response.ok) {
                const data = await response.text();
                await fetch(`database/${filename}.backup`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: data
                });
            }
        } catch (error) {
            console.warn('Backup creation failed:', error);
        }
    }

    /**
     * Restore from backup
     */
    async restoreBackup(filename) {
        try {
            const response = await fetch(`database/${filename}.backup`);
            if (response.ok) {
                const data = await response.text();
                await fetch(`database/${filename}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: data
                });
            }
        } catch (error) {
            console.error('Backup restoration failed:', error);
        }
    }

    /**
     * Add project with atomic operation
     */
    async addProject(project) {
        const projects = await this.atomicRead('projects.json');
        
        // Add the new project
        projects.projects[project.id] = project;
        projects.metadata.totalProjects = Object.keys(projects.projects).length;
        projects.metadata.lastModified = new Date().toISOString();
        
        await this.atomicWrite('projects.json', projects);
        
        // Update analytics
        await this.updateAnalytics();
        
        return true;
    }

    /**
     * Update project with atomic operation
     */
    async updateProject(projectId, updates) {
        const projects = await this.atomicRead('projects.json');
        
        if (!projects.projects[projectId]) {
            throw new Error('Project not found: ' + projectId);
        }
        
        // Merge updates
        projects.projects[projectId] = {
            ...projects.projects[projectId],
            ...updates,
            dateModified: new Date().toISOString().split('T')[0]
        };
        
        projects.metadata.lastModified = new Date().toISOString();
        
        await this.atomicWrite('projects.json', projects);
        
        // Update analytics
        await this.updateAnalytics();
        
        return projects.projects[projectId];
    }

    /**
     * Add review with atomic operation
     */
    async addReview(projectId, review) {
        const projects = await this.atomicRead('projects.json');
        
        if (!projects.projects[projectId]) {
            throw new Error('Project not found: ' + projectId);
        }
        
        if (!projects.projects[projectId].reviews) {
            projects.projects[projectId].reviews = [];
        }
        
        // Add review with timestamp
        const reviewWithTimestamp = {
            ...review,
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
            date: new Date().toISOString().split('T')[0]
        };
        
        projects.projects[projectId].reviews.push(reviewWithTimestamp);
        projects.projects[projectId].dateModified = new Date().toISOString().split('T')[0];
        projects.metadata.lastModified = new Date().toISOString();
        
        await this.atomicWrite('projects.json', projects);
        
        // Update analytics
        await this.updateAnalytics();
        
        return reviewWithTimestamp;
    }

    /**
     * Update analytics based on current projects
     */
    async updateAnalytics() {
        try {
            const projects = await this.atomicRead('projects.json');
            const analytics = await this.atomicRead('analytics.json');
            
            // Calculate new analytics
            const projectList = Object.values(projects.projects);
            const fieldCounts = {};
            const statusCounts = {};
            const authorSet = new Set();
            let totalCompleteness = 0;
            
            projectList.forEach(project => {
                // Count fields
                fieldCounts[project.field] = (fieldCounts[project.field] || 0) + 1;
                
                // Count statuses
                statusCounts[project.status] = (statusCounts[project.status] || 0) + 1;
                
                // Count authors
                project.contributors.forEach(c => {
                    const name = c.name === 'Google Gemini' ? 'Gemini' : c.name;
                    authorSet.add(name);
                });
                
                // Sum completeness
                totalCompleteness += project.completeness || 0;
            });
            
            // Update analytics
            analytics.stats = {
                totalProjects: projectList.length,
                totalCompleteness: Math.round(totalCompleteness / projectList.length),
                uniqueAuthors: authorSet.size,
                uniqueFields: Object.keys(fieldCounts).length
            };
            
            analytics.projectsByField = fieldCounts;
            analytics.projectsByStatus = statusCounts;
            analytics.metadata.lastUpdated = new Date().toISOString();
            
            await this.atomicWrite('analytics.json', analytics);
            
        } catch (error) {
            console.error('Failed to update analytics:', error);
        }
    }
}

// Create global instance for browsers that support it
if (typeof window !== 'undefined') {
    window.DatabaseManager = new DatabaseManager();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DatabaseManager;
}

console.log('🔒 DatabaseManager loaded with concurrency control');