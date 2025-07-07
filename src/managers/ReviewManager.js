/**
 * ReviewManager - Manages automated and manual review workflows
 * 
 * Handles review submission, validation, point calculation, and phase advancement
 * for the llmXive system.
 */

class ReviewManager {
    constructor(fileManager, systemConfig, projectManager) {
        this.fileManager = fileManager;
        this.systemConfig = systemConfig;
        this.projectManager = projectManager;
        this.reviewTypesPath = '.llmxive-system/registry/review-types.json';
        this.reviewHistory = new Map();
    }
    
    /**
     * Submit a review for a project phase
     */
    async submitReview(reviewData) {
        try {
            // Validate review data
            await this.validateReviewData(reviewData);
            
            // Generate review ID
            const reviewId = this.generateReviewId(reviewData);
            
            // Get review type configuration
            const reviewTypes = await this.getReviewTypes();
            const reviewType = reviewTypes.review_types[reviewData.type];
            
            if (!reviewType) {
                throw new Error(`Unknown review type: ${reviewData.type}`);
            }
            
            // Create review document
            const reviewDoc = await this.createReviewDocument(reviewId, reviewData, reviewType);
            
            // Write review file
            const reviewPath = this.getReviewPath(reviewData.projectId, reviewData.automated, reviewId);
            await this.fileManager.writeJSON(
                reviewPath,
                reviewDoc,
                `Submit ${reviewData.automated ? 'automated' : 'manual'} review for ${reviewData.projectId}`,
                true
            );
            
            // Update project with review
            await this.updateProjectReviews(reviewData.projectId, reviewData.phase, reviewDoc);
            
            // Check for phase advancement
            await this.checkPhaseAdvancement(reviewData.projectId, reviewData.phase);
            
            // Log review submission
            await this.fileManager.appendToLog('.llmxive-system/logs/reviews.json', {
                type: 'review_submitted',
                reviewId: reviewId,
                projectId: reviewData.projectId,
                phase: reviewData.phase,
                reviewType: reviewData.type,
                automated: reviewData.automated,
                points: reviewType.point_value,
                reviewer: reviewData.reviewer
            });
            
            console.log(`Review submitted successfully: ${reviewId}`);
            return {
                reviewId,
                points: reviewType.point_value,
                status: 'submitted',
                path: reviewPath
            };
            
        } catch (error) {
            console.error('Failed to submit review:', error);
            throw error;
        }
    }
    
    /**
     * Validate review data
     */
    async validateReviewData(reviewData) {
        const requiredFields = ['projectId', 'phase', 'type', 'content', 'reviewer'];
        
        for (const field of requiredFields) {
            if (!reviewData[field]) {
                throw new Error(`Missing required field: ${field}`);
            }
        }
        
        // Check if project exists
        const project = await this.projectManager.getProject(reviewData.projectId);
        if (!project) {
            throw new Error(`Project not found: ${reviewData.projectId}`);
        }
        
        // Check if phase exists and is valid for review
        if (!project.phases[reviewData.phase]) {
            throw new Error(`Invalid phase: ${reviewData.phase}`);
        }
        
        const phase = project.phases[reviewData.phase];
        if (phase.status === 'pending') {
            throw new Error(`Phase ${reviewData.phase} is not yet active`);
        }
        
        // Validate review content
        if (typeof reviewData.content !== 'object' || !reviewData.content.summary) {
            throw new Error('Review content must include a summary');
        }
        
        return true;
    }
    
    /**
     * Generate unique review ID
     */
    generateReviewId(reviewData) {
        const date = new Date();
        const dateString = date.toISOString().split('T')[0];
        const timeString = date.toTimeString().split(' ')[0].replace(/:/g, '');
        const reviewerSlug = reviewData.reviewer.toLowerCase().replace(/[^a-z0-9]/g, '');
        const typeCode = reviewData.automated ? 'A' : 'M';
        
        return `${reviewData.type}_${reviewData.phase}_${dateString}_${timeString}_${reviewerSlug}_${typeCode}`;
    }
    
    /**
     * Create review document
     */
    async createReviewDocument(reviewId, reviewData, reviewType) {
        const doc = {
            id: reviewId,
            metadata: {
                projectId: reviewData.projectId,
                phase: reviewData.phase,
                reviewType: reviewData.type,
                automated: reviewData.automated,
                reviewer: reviewData.reviewer,
                submittedDate: new Date().toISOString(),
                pointValue: reviewType.point_value
            },
            content: {
                summary: reviewData.content.summary,
                details: reviewData.content.details || '',
                strengths: reviewData.content.strengths || [],
                weaknesses: reviewData.content.weaknesses || [],
                recommendations: reviewData.content.recommendations || [],
                rating: reviewData.content.rating || null,
                confidence: reviewData.content.confidence || null
            },
            criteria: {
                technical_quality: reviewData.content.criteria?.technical_quality || null,
                clarity: reviewData.content.criteria?.clarity || null,
                completeness: reviewData.content.criteria?.completeness || null,
                feasibility: reviewData.content.criteria?.feasibility || null,
                innovation: reviewData.content.criteria?.innovation || null
            },
            decision: {
                approved: reviewData.content.decision?.approved || false,
                conditional: reviewData.content.decision?.conditional || false,
                major_revisions: reviewData.content.decision?.major_revisions || false,
                reject: reviewData.content.decision?.reject || false,
                comments: reviewData.content.decision?.comments || ''
            }
        };
        
        // Add automated review specific fields
        if (reviewData.automated) {
            doc.automation = {
                model: reviewData.model || 'unknown',
                modelVersion: reviewData.modelVersion || 'unknown',
                processingTime: reviewData.processingTime || null,
                confidence: reviewData.confidence || null,
                prompt: reviewData.prompt || null
            };
        }
        
        return doc;
    }
    
    /**
     * Get review file path
     */
    getReviewPath(projectId, automated, reviewId) {
        const reviewDir = automated ? 'automated' : 'manual';
        return `projects/${projectId}/reviews/${reviewDir}/${reviewId}.json`;
    }
    
    /**
     * Update project with new review
     */
    async updateProjectReviews(projectId, phaseId, reviewDoc) {
        const project = await this.projectManager.getProject(projectId);
        
        if (!project || !project.phases[phaseId]) {
            throw new Error(`Invalid project or phase: ${projectId}/${phaseId}`);
        }
        
        // Add review to phase
        const reviewType = reviewDoc.metadata.automated ? 'automated' : 'manual';
        project.phases[phaseId].reviews[reviewType].push({
            id: reviewDoc.id,
            type: reviewDoc.metadata.reviewType,
            reviewer: reviewDoc.metadata.reviewer,
            submitted_date: reviewDoc.metadata.submittedDate,
            points: reviewDoc.metadata.pointValue,
            approved: reviewDoc.decision.approved,
            rating: reviewDoc.content.rating
        });
        
        // Update total points
        project.phases[phaseId].reviews.total_points += reviewDoc.metadata.pointValue;
        
        // Update project metrics
        project.metrics.total_reviews += 1;
        project.metrics.total_points += reviewDoc.metadata.pointValue;
        
        // Save updated project
        await this.projectManager.updateProject(projectId, project);
    }
    
    /**
     * Check if phase can advance and update status
     */
    async checkPhaseAdvancement(projectId, phaseId) {
        const project = await this.projectManager.getProject(projectId);
        
        if (!project || !project.phases[phaseId]) {
            return false;
        }
        
        const phase = project.phases[phaseId];
        
        // Check if phase meets advancement criteria
        const canAdvance = await this.canPhaseAdvance(project, phaseId);
        
        if (canAdvance && phase.status === 'in_progress') {
            // Mark current phase as completed
            phase.status = 'completed';
            phase.completed_date = new Date().toISOString();
            
            // Start next phase if it exists
            const phaseIds = Object.keys(project.phases);
            const currentIndex = phaseIds.indexOf(phaseId);
            
            if (currentIndex < phaseIds.length - 1) {
                const nextPhaseId = phaseIds[currentIndex + 1];
                project.phases[nextPhaseId].status = 'in_progress';
                project.phases[nextPhaseId].started_date = new Date().toISOString();
                
                console.log(`Phase advancement: ${phaseId} → ${nextPhaseId} for project ${projectId}`);
                
                // Log phase advancement
                await this.fileManager.appendToLog('.llmxive-system/logs/projects.json', {
                    type: 'phase_advanced',
                    projectId: projectId,
                    fromPhase: phaseId,
                    toPhase: nextPhaseId,
                    totalPoints: phase.reviews.total_points
                });
            } else {
                // All phases completed
                project.project.status = 'completed';
                
                console.log(`Project completed: ${projectId}`);
                
                // Log project completion
                await this.fileManager.appendToLog('.llmxive-system/logs/projects.json', {
                    type: 'project_completed',
                    projectId: projectId,
                    totalPhases: phaseIds.length,
                    totalReviews: project.metrics.total_reviews,
                    totalPoints: project.metrics.total_points
                });
            }
            
            // Save updated project
            await this.projectManager.updateProject(projectId, project);
            
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if phase can advance based on review points and requirements
     */
    async canPhaseAdvance(project, phaseId) {
        const phase = project.phases[phaseId];
        
        // Check if minimum points requirement is met
        if (phase.reviews.total_points < phase.reviews.required_points) {
            return false;
        }
        
        // Check if required artifacts exist
        const pipelineStages = await this.getPipelineStages();
        const stageConfig = pipelineStages.stages[phaseId];
        
        if (stageConfig && stageConfig.required_artifacts) {
            for (const artifact of stageConfig.required_artifacts) {
                const artifactExists = await this.checkArtifactExists(project.project.id, artifact);
                if (!artifactExists) {
                    console.log(`Missing required artifact: ${artifact} for phase ${phaseId}`);
                    return false;
                }
            }
        }
        
        // Check if minimum number of reviews is met
        const totalReviews = phase.reviews.automated.length + phase.reviews.manual.length;
        if (totalReviews < (stageConfig?.review_requirements?.min_reviews || 3)) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Check if artifact exists
     */
    async checkArtifactExists(projectId, artifactPath) {
        try {
            const fullPath = `projects/${projectId}/${artifactPath}`;
            return await this.fileManager.fileExists(fullPath);
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Get review types configuration
     */
    async getReviewTypes() {
        try {
            return await this.fileManager.readJSON(this.reviewTypesPath);
        } catch (error) {
            console.error('Failed to load review types:', error);
            throw error;
        }
    }
    
    /**
     * Get pipeline stages configuration
     */
    async getPipelineStages() {
        try {
            return await this.fileManager.readJSON('.llmxive-system/registry/pipeline-stages.json');
        } catch (error) {
            console.error('Failed to load pipeline stages:', error);
            throw error;
        }
    }
    
    /**
     * Get reviews for a project phase
     */
    async getPhaseReviews(projectId, phaseId) {
        try {
            const automatedPath = `projects/${projectId}/reviews/automated`;
            const manualPath = `projects/${projectId}/reviews/manual`;
            
            const [automatedFiles, manualFiles] = await Promise.all([
                this.fileManager.listDirectory(automatedPath).catch(() => []),
                this.fileManager.listDirectory(manualPath).catch(() => [])
            ]);
            
            // Filter reviews for the specific phase
            const phaseAutomated = automatedFiles.filter(file => 
                file.name.includes(phaseId) && file.name.endsWith('.json')
            );
            
            const phaseManual = manualFiles.filter(file => 
                file.name.includes(phaseId) && file.name.endsWith('.json')
            );
            
            // Load review content
            const automatedReviews = await Promise.all(
                phaseAutomated.map(file => 
                    this.fileManager.readJSON(`${automatedPath}/${file.name}`)
                )
            );
            
            const manualReviews = await Promise.all(
                phaseManual.map(file => 
                    this.fileManager.readJSON(`${manualPath}/${file.name}`)
                )
            );
            
            return {
                automated: automatedReviews,
                manual: manualReviews,
                total: automatedReviews.length + manualReviews.length
            };
            
        } catch (error) {
            console.error(`Failed to get reviews for ${projectId}/${phaseId}:`, error);
            return { automated: [], manual: [], total: 0 };
        }
    }
    
    /**
     * Get all reviews for a project
     */
    async getProjectReviews(projectId) {
        try {
            const project = await this.projectManager.getProject(projectId);
            if (!project) {
                throw new Error(`Project not found: ${projectId}`);
            }
            
            const reviews = {};
            
            for (const phaseId of Object.keys(project.phases)) {
                reviews[phaseId] = await this.getPhaseReviews(projectId, phaseId);
            }
            
            return reviews;
            
        } catch (error) {
            console.error(`Failed to get project reviews for ${projectId}:`, error);
            throw error;
        }
    }
    
    /**
     * Calculate review statistics
     */
    async getReviewStatistics(projectId = null) {
        try {
            if (projectId) {
                // Statistics for specific project
                const project = await this.projectManager.getProject(projectId);
                if (!project) {
                    throw new Error(`Project not found: ${projectId}`);
                }
                
                return {
                    projectId: projectId,
                    totalReviews: project.metrics.total_reviews,
                    totalPoints: project.metrics.total_points,
                    averagePointsPerReview: project.metrics.total_reviews > 0 
                        ? project.metrics.total_points / project.metrics.total_reviews 
                        : 0,
                    phaseBreakdown: this.calculatePhaseReviewBreakdown(project.phases)
                };
            } else {
                // System-wide statistics
                const projects = await this.projectManager.listProjects();
                
                let totalReviews = 0;
                let totalPoints = 0;
                let automatedReviews = 0;
                let manualReviews = 0;
                
                for (const project of projects) {
                    const fullProject = await this.projectManager.getProject(project.id);
                    if (fullProject) {
                        totalReviews += fullProject.metrics.total_reviews;
                        totalPoints += fullProject.metrics.total_points;
                        
                        // Count automated vs manual reviews
                        Object.values(fullProject.phases).forEach(phase => {
                            automatedReviews += phase.reviews.automated.length;
                            manualReviews += phase.reviews.manual.length;
                        });
                    }
                }
                
                return {
                    totalProjects: projects.length,
                    totalReviews: totalReviews,
                    totalPoints: totalPoints,
                    automatedReviews: automatedReviews,
                    manualReviews: manualReviews,
                    averagePointsPerReview: totalReviews > 0 ? totalPoints / totalReviews : 0,
                    averageReviewsPerProject: projects.length > 0 ? totalReviews / projects.length : 0
                };
            }
            
        } catch (error) {
            console.error('Failed to calculate review statistics:', error);
            throw error;
        }
    }
    
    /**
     * Calculate phase review breakdown
     */
    calculatePhaseReviewBreakdown(phases) {
        const breakdown = {};
        
        Object.entries(phases).forEach(([phaseId, phase]) => {
            breakdown[phaseId] = {
                automated: phase.reviews.automated.length,
                manual: phase.reviews.manual.length,
                totalPoints: phase.reviews.total_points,
                requiredPoints: phase.reviews.required_points,
                canAdvance: phase.reviews.total_points >= phase.reviews.required_points
            };
        });
        
        return breakdown;
    }
}

export default ReviewManager;