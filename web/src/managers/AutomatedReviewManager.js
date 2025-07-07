/**
 * AutomatedReviewManager - Generates automated reviews using AI models
 * 
 * Orchestrates the automated review process by combining the ModelManager
 * and ReviewManager to generate intelligent project reviews.
 */

class AutomatedReviewManager {
    constructor(fileManager, systemConfig, projectManager, reviewManager, modelManager) {
        this.fileManager = fileManager;
        this.systemConfig = systemConfig;
        this.projectManager = projectManager;
        this.reviewManager = reviewManager;
        this.modelManager = modelManager;
        
        // Review templates and prompts
        this.reviewTemplates = new Map();
        this.reviewCriteria = new Map();
        
        // Processing queue for batch operations
        this.processingQueue = [];
        this.isProcessing = false;
        
        this.initializeTemplates();
    }
    
    /**
     * Initialize review templates and criteria
     */
    initializeTemplates() {
        // Concept validation template
        this.reviewTemplates.set('concept_validation', {
            systemPrompt: `You are an expert research reviewer evaluating a project concept for scientific merit and feasibility.`,
            userPrompt: `Please review the following project concept and provide a detailed evaluation:

**Project Title:** {title}
**Description:** {description}
**Phase:** Concept/Ideation

**Evaluation Criteria:**
1. **Scientific Merit** (1-5): Is this addressing an important research question?
2. **Novelty** (1-5): How original is this approach?
3. **Feasibility** (1-5): Can this realistically be completed?
4. **Clarity** (1-5): Is the concept clearly articulated?
5. **Impact Potential** (1-5): What is the potential impact of this research?

**Content to Review:**
{content}

**Required Output Format:**
Provide your review in this exact JSON format:
\`\`\`json
{
  "summary": "Brief 2-3 sentence summary of your assessment",
  "scores": {
    "scientific_merit": 4,
    "novelty": 3,
    "feasibility": 4,
    "clarity": 3,
    "impact_potential": 4
  },
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "decision": {
    "approved": true,
    "conditional": false,
    "major_revisions": false,
    "reject": false,
    "comments": "Overall assessment and recommendation"
  },
  "detailed_feedback": "Comprehensive paragraph explaining your evaluation"
}
\`\`\``,
            requiredCapabilities: ['text_generation', 'research'],
            estimatedTokens: 800,
            pointValue: 0.5
        });
        
        // Technical review template
        this.reviewTemplates.set('technical_review', {
            systemPrompt: `You are a senior technical reviewer with expertise in software architecture, algorithms, and research methodology.`,
            userPrompt: `Please conduct a comprehensive technical review of this project design:

**Project:** {title}
**Phase:** Technical Design
**Description:** {description}

**Technical Design Document:**
{content}

**Evaluation Criteria:**
1. **Technical Soundness** (1-5): Are the proposed methods technically sound?
2. **Architecture Quality** (1-5): Is the system architecture well-designed?
3. **Scalability** (1-5): Will this approach scale appropriately?
4. **Implementation Details** (1-5): Are implementation details sufficient?
5. **Risk Assessment** (1-5): Have technical risks been properly identified?

**Required Output Format:**
\`\`\`json
{
  "summary": "Technical assessment summary",
  "scores": {
    "technical_soundness": 4,
    "architecture_quality": 3,
    "scalability": 4,
    "implementation_details": 3,
    "risk_assessment": 4
  },
  "strengths": ["technical strength 1", "technical strength 2"],
  "weaknesses": ["technical weakness 1", "technical weakness 2"],
  "recommendations": ["technical recommendation 1", "technical recommendation 2"],
  "decision": {
    "approved": true,
    "conditional": false,
    "major_revisions": false,
    "reject": false,
    "comments": "Technical recommendation"
  },
  "detailed_feedback": "Detailed technical analysis"
}
\`\`\``,
            requiredCapabilities: ['text_generation', 'code_analysis'],
            estimatedTokens: 1200,
            pointValue: 1.0
        });
        
        // Code review template
        this.reviewTemplates.set('code_review', {
            systemPrompt: `You are an expert code reviewer focusing on quality, security, and best practices.`,
            userPrompt: `Please review the following code implementation:

**Project:** {title}
**Phase:** Implementation
**Files to Review:** {fileList}

**Code Content:**
{content}

**Evaluation Criteria:**
1. **Code Quality** (1-5): Overall code quality and structure
2. **Security** (1-5): Security considerations and vulnerabilities
3. **Performance** (1-5): Performance and efficiency
4. **Maintainability** (1-5): Code maintainability and readability
5. **Testing** (1-5): Test coverage and quality

**Required Output Format:**
\`\`\`json
{
  "summary": "Code review summary",
  "scores": {
    "code_quality": 4,
    "security": 4,
    "performance": 3,
    "maintainability": 4,
    "testing": 3
  },
  "strengths": ["code strength 1", "code strength 2"],
  "weaknesses": ["code weakness 1", "code weakness 2"],
  "recommendations": ["code recommendation 1", "code recommendation 2"],
  "security_issues": ["security issue 1", "security issue 2"],
  "performance_notes": ["performance note 1"],
  "decision": {
    "approved": true,
    "conditional": false,
    "major_revisions": false,
    "reject": false,
    "comments": "Code review recommendation"
  },
  "detailed_feedback": "Detailed code analysis"
}
\`\`\``,
            requiredCapabilities: ['code_analysis', 'text_generation'],
            estimatedTokens: 1500,
            pointValue: 1.0
        });
        
        // Paper review template
        this.reviewTemplates.set('paper_review', {
            systemPrompt: `You are an academic peer reviewer with expertise in evaluating research papers for publication.`,
            userPrompt: `Please conduct a thorough academic review of this research paper:

**Title:** {title}
**Authors:** {authors}
**Abstract:** {abstract}

**Paper Content:**
{content}

**Evaluation Criteria:**
1. **Significance** (1-5): Importance and relevance of the research
2. **Methodology** (1-5): Soundness of experimental design and methods
3. **Results** (1-5): Quality and interpretation of results
4. **Writing Quality** (1-5): Clarity, organization, and presentation
5. **Reproducibility** (1-5): Can the work be reproduced from the description?

**Required Output Format:**
\`\`\`json
{
  "summary": "Academic review summary",
  "scores": {
    "significance": 4,
    "methodology": 4,
    "results": 3,
    "writing_quality": 4,
    "reproducibility": 3
  },
  "strengths": ["research strength 1", "research strength 2"],
  "weaknesses": ["research weakness 1", "research weakness 2"],
  "recommendations": ["research recommendation 1", "research recommendation 2"],
  "methodological_concerns": ["concern 1", "concern 2"],
  "suggested_improvements": ["improvement 1", "improvement 2"],
  "decision": {
    "approved": true,
    "conditional": false,
    "major_revisions": false,
    "reject": false,
    "comments": "Publication recommendation"
  },
  "detailed_feedback": "Comprehensive academic assessment"
}
\`\`\``,
            requiredCapabilities: ['text_generation', 'research'],
            estimatedTokens: 2000,
            pointValue: 1.5
        });
    }
    
    /**
     * Generate automated review for a project phase
     */
    async generateAutomatedReview(projectId, phase, reviewType) {
        try {
            console.log(`Generating automated review: ${reviewType} for ${projectId}/${phase}`);
            
            // Get project data
            const project = await this.projectManager.getProject(projectId);
            if (!project) {
                throw new Error(`Project not found: ${projectId}`);
            }
            
            // Check if phase is ready for review
            if (!this.isPhaseReadyForReview(project, phase)) {
                throw new Error(`Phase ${phase} is not ready for review`);
            }
            
            // Get review template
            const template = this.reviewTemplates.get(reviewType);
            if (!template) {
                throw new Error(`Unknown review type: ${reviewType}`);
            }
            
            // Collect content for review
            const content = await this.collectReviewContent(projectId, phase);
            
            // Prepare prompt
            const prompt = this.prepareReviewPrompt(template, project, content);
            
            // Select appropriate model
            const model = await this.modelManager.selectModelForTask(reviewType, {
                contextWindow: template.estimatedTokens * 2,
                minQuality: 0.8
            });
            
            // Execute model call
            const modelResponse = await this.modelManager.executeModelCall(
                model.id,
                prompt,
                {
                    maxTokens: 1000,
                    temperature: 0.1,
                    priority: 'normal'
                }
            );
            
            // Parse and validate response
            const reviewContent = this.parseModelResponse(modelResponse.response.content);
            
            // Create review document
            const reviewData = {
                projectId: projectId,
                phase: phase,
                type: reviewType,
                automated: true,
                reviewer: `${model.name}-${model.id}`,
                model: model.id,
                modelVersion: model.version || '1.0',
                processingTime: modelResponse.metadata.processingTime,
                confidence: this.calculateConfidence(reviewContent),
                content: reviewContent,
                prompt: this.sanitizePrompt(prompt)
            };
            
            // Submit review through ReviewManager
            const reviewResult = await this.reviewManager.submitReview(reviewData);
            
            // Log successful review generation
            await this.logReviewGeneration(projectId, phase, reviewType, model.id, 'success');
            
            console.log(`Automated review generated successfully: ${reviewResult.reviewId}`);
            
            return {
                success: true,
                reviewId: reviewResult.reviewId,
                model: model.id,
                points: reviewResult.points,
                confidence: reviewData.confidence,
                metadata: modelResponse.metadata
            };
            
        } catch (error) {
            console.error(`Failed to generate automated review: ${error.message}`);
            
            // Log failed review generation
            await this.logReviewGeneration(projectId, phase, reviewType, null, 'error', error.message);
            
            throw error;
        }
    }
    
    /**
     * Check if phase is ready for automated review
     */
    isPhaseReadyForReview(project, phase) {
        const phaseData = project.phases[phase];
        if (!phaseData) {
            return false;
        }
        
        // Phase must be in progress or completed
        if (phaseData.status === 'pending') {
            return false;
        }
        
        // Check if required artifacts exist
        return phaseData.artifacts && phaseData.artifacts.length > 0;
    }
    
    /**
     * Collect content for review
     */
    async collectReviewContent(projectId, phase) {
        const content = {};
        
        try {
            switch (phase) {
                case 'idea':
                    content.idea = await this.fileManager.readJSON(`projects/${projectId}/idea/initial-idea.md`);
                    content.brainstorming = await this.collectBrainstormingContent(projectId);
                    break;
                    
                case 'design':
                    content.technicalDesign = await this.fileManager.readJSON(`projects/${projectId}/technical-design/main.md`);
                    content.diagrams = await this.collectDiagrams(projectId);
                    content.specifications = await this.collectSpecifications(projectId);
                    break;
                    
                case 'implementation_plan':
                    content.implementationPlan = await this.fileManager.readJSON(`projects/${projectId}/implementation-plan/main.md`);
                    content.milestones = await this.collectMilestones(projectId);
                    content.tasks = await this.collectTasks(projectId);
                    break;
                    
                case 'implementation':
                    content.sourceCode = await this.collectSourceCode(projectId);
                    content.tests = await this.collectTests(projectId);
                    content.notebooks = await this.collectNotebooks(projectId);
                    content.data = await this.collectDataSummary(projectId);
                    break;
                    
                case 'paper':
                    content.paper = await this.collectPaperContent(projectId);
                    content.figures = await this.collectFigures(projectId);
                    content.bibliography = await this.collectBibliography(projectId);
                    break;
                    
                default:
                    throw new Error(`Unknown phase: ${phase}`);
            }
            
            return content;
            
        } catch (error) {
            console.error(`Failed to collect review content for ${projectId}/${phase}:`, error);
            return {};
        }
    }
    
    /**
     * Prepare review prompt from template
     */
    prepareReviewPrompt(template, project, content) {
        let prompt = template.systemPrompt + '\n\n' + template.userPrompt;
        
        // Replace placeholders
        prompt = prompt.replace(/{title}/g, project.project.title);
        prompt = prompt.replace(/{description}/g, project.project.description);
        prompt = prompt.replace(/{content}/g, this.formatContentForPrompt(content));
        
        // Add authors if available
        if (project.contributors) {
            const authors = project.contributors
                .filter(c => c.type === 'human')
                .map(c => c.name)
                .join(', ');
            prompt = prompt.replace(/{authors}/g, authors);
        }
        
        // Add file list for code reviews
        if (content.sourceCode) {
            const fileList = Object.keys(content.sourceCode).join(', ');
            prompt = prompt.replace(/{fileList}/g, fileList);
        }
        
        return prompt;
    }
    
    /**
     * Format content for inclusion in prompt
     */
    formatContentForPrompt(content) {
        let formatted = '';
        
        for (const [key, value] of Object.entries(content)) {
            if (value && typeof value === 'string') {
                formatted += `\n## ${key}:\n${value}\n`;
            } else if (value && typeof value === 'object') {
                formatted += `\n## ${key}:\n${JSON.stringify(value, null, 2)}\n`;
            }
        }
        
        // Limit content length to prevent token overflow
        if (formatted.length > 10000) {
            formatted = formatted.substring(0, 10000) + '\n\n[Content truncated due to length]';
        }
        
        return formatted;
    }
    
    /**
     * Parse model response and validate format
     */
    parseModelResponse(responseText) {
        try {
            // Extract JSON from response
            const jsonMatch = responseText.match(/```json\s*(\{[\s\S]*?\})\s*```/);
            if (!jsonMatch) {
                throw new Error('No JSON found in model response');
            }
            
            const reviewData = JSON.parse(jsonMatch[1]);
            
            // Validate required fields
            this.validateReviewData(reviewData);
            
            return reviewData;
            
        } catch (error) {
            console.error('Failed to parse model response:', error);
            
            // Fallback: create basic review from text
            return this.createFallbackReview(responseText);
        }
    }
    
    /**
     * Validate review data structure
     */
    validateReviewData(reviewData) {
        const requiredFields = ['summary', 'scores', 'strengths', 'weaknesses', 'recommendations', 'decision'];
        
        for (const field of requiredFields) {
            if (!reviewData[field]) {
                throw new Error(`Missing required field: ${field}`);
            }
        }
        
        // Validate scores are numbers between 1-5
        if (reviewData.scores) {
            for (const [criterion, score] of Object.entries(reviewData.scores)) {
                if (typeof score !== 'number' || score < 1 || score > 5) {
                    throw new Error(`Invalid score for ${criterion}: ${score}`);
                }
            }
        }
        
        // Validate decision structure
        if (!reviewData.decision || typeof reviewData.decision !== 'object') {
            throw new Error('Invalid decision structure');
        }
    }
    
    /**
     * Create fallback review when parsing fails
     */
    createFallbackReview(responseText) {
        return {
            summary: 'Automated review generated (parsing fallback)',
            scores: {
                overall_quality: 3
            },
            strengths: ['Review generated by AI model'],
            weaknesses: ['Response format could not be parsed'],
            recommendations: ['Manual review recommended'],
            decision: {
                approved: false,
                conditional: true,
                major_revisions: false,
                reject: false,
                comments: 'Automated review requires manual verification'
            },
            detailed_feedback: responseText.substring(0, 1000),
            parsing_error: true
        };
    }
    
    /**
     * Calculate confidence score for review
     */
    calculateConfidence(reviewContent) {
        let confidence = 0.5; // Base confidence
        
        // Increase confidence for well-structured responses
        if (reviewContent.scores && Object.keys(reviewContent.scores).length > 0) {
            confidence += 0.2;
        }
        
        if (reviewContent.strengths && reviewContent.strengths.length > 0) {
            confidence += 0.1;
        }
        
        if (reviewContent.recommendations && reviewContent.recommendations.length > 0) {
            confidence += 0.1;
        }
        
        if (reviewContent.detailed_feedback && reviewContent.detailed_feedback.length > 100) {
            confidence += 0.1;
        }
        
        // Decrease confidence for parsing errors
        if (reviewContent.parsing_error) {
            confidence -= 0.3;
        }
        
        return Math.min(Math.max(confidence, 0.0), 1.0);
    }
    
    /**
     * Sanitize prompt for logging (remove sensitive information)
     */
    sanitizePrompt(prompt) {
        // Remove system prompts and limit length for logging
        const userPromptStart = prompt.indexOf('Please review');
        if (userPromptStart > 0) {
            prompt = prompt.substring(userPromptStart);
        }
        
        return prompt.length > 500 ? prompt.substring(0, 500) + '...' : prompt;
    }
    
    /**
     * Generate reviews for all eligible projects (for GitHub Actions)
     */
    async generateBatchReviews(options = {}) {
        try {
            console.log('Starting batch review generation...');
            
            const projects = await this.projectManager.listProjects();
            const reviewsGenerated = [];
            const errors = [];
            
            for (const project of projects) {
                try {
                    const fullProject = await this.projectManager.getProject(project.id);
                    if (!fullProject) continue;
                    
                    // Check each phase for review opportunities
                    for (const [phaseId, phase] of Object.entries(fullProject.phases)) {
                        if (this.needsAutomatedReview(phase, options)) {
                            const reviewTypes = this.getRequiredReviewTypes(phaseId);
                            
                            for (const reviewType of reviewTypes) {
                                try {
                                    const result = await this.generateAutomatedReview(
                                        project.id, 
                                        phaseId, 
                                        reviewType
                                    );
                                    
                                    reviewsGenerated.push({
                                        projectId: project.id,
                                        phase: phaseId,
                                        reviewType: reviewType,
                                        reviewId: result.reviewId,
                                        model: result.model,
                                        points: result.points
                                    });
                                    
                                } catch (reviewError) {
                                    errors.push({
                                        projectId: project.id,
                                        phase: phaseId,
                                        reviewType: reviewType,
                                        error: reviewError.message
                                    });
                                }
                            }
                        }
                    }
                    
                } catch (projectError) {
                    errors.push({
                        projectId: project.id,
                        error: projectError.message
                    });
                }
            }
            
            // Log batch results
            await this.logBatchResults(reviewsGenerated, errors);
            
            console.log(`Batch review generation completed: ${reviewsGenerated.length} reviews generated, ${errors.length} errors`);
            
            return {
                success: true,
                reviewsGenerated: reviewsGenerated.length,
                errors: errors.length,
                details: { reviewsGenerated, errors }
            };
            
        } catch (error) {
            console.error('Batch review generation failed:', error);
            throw error;
        }
    }
    
    /**
     * Check if phase needs automated review
     */
    needsAutomatedReview(phase, options = {}) {
        // Phase must be active or completed
        if (phase.status === 'pending') {
            return false;
        }
        
        // Check if enough time has passed since last review
        const minTimeBetweenReviews = options.minTimeBetweenReviews || 24 * 60 * 60 * 1000; // 24 hours
        const lastReview = this.getLastAutomatedReview(phase);
        
        if (lastReview) {
            const timeSinceLastReview = Date.now() - new Date(lastReview.submitted_date).getTime();
            if (timeSinceLastReview < minTimeBetweenReviews) {
                return false;
            }
        }
        
        // Check if manual reviews are sufficient
        const manualReviews = phase.reviews.manual.length;
        const automatedReviews = phase.reviews.automated.length;
        
        // Need automated reviews if we have fewer than required total reviews
        const requiredReviews = phase.reviews.required_points * 2; // Rough estimate
        const totalReviews = manualReviews + automatedReviews;
        
        return totalReviews < requiredReviews;
    }
    
    /**
     * Get last automated review for phase
     */
    getLastAutomatedReview(phase) {
        if (!phase.reviews.automated || phase.reviews.automated.length === 0) {
            return null;
        }
        
        return phase.reviews.automated
            .sort((a, b) => new Date(b.submitted_date) - new Date(a.submitted_date))[0];
    }
    
    /**
     * Get required review types for phase
     */
    getRequiredReviewTypes(phaseId) {
        const reviewTypeMap = {
            'idea': ['concept_validation'],
            'design': ['technical_review'],
            'implementation_plan': ['technical_review'],
            'implementation': ['code_review'],
            'paper': ['paper_review'],
            'review': ['comprehensive_review']
        };
        
        return reviewTypeMap[phaseId] || ['concept_validation'];
    }
    
    /**
     * Log review generation attempt
     */
    async logReviewGeneration(projectId, phase, reviewType, modelId, status, error = null) {
        const logEntry = {
            type: 'automated_review_generation',
            projectId: projectId,
            phase: phase,
            reviewType: reviewType,
            modelId: modelId,
            status: status,
            error: error,
            timestamp: new Date().toISOString()
        };
        
        try {
            await this.fileManager.appendToLog('.llmxive-system/logs/automated-reviews.json', logEntry);
        } catch (logError) {
            console.error('Failed to log review generation:', logError);
        }
    }
    
    /**
     * Log batch processing results
     */
    async logBatchResults(reviewsGenerated, errors) {
        const logEntry = {
            type: 'batch_review_generation',
            reviewsGenerated: reviewsGenerated.length,
            errors: errors.length,
            details: {
                reviews: reviewsGenerated,
                errors: errors
            },
            timestamp: new Date().toISOString()
        };
        
        try {
            await this.fileManager.appendToLog('.llmxive-system/logs/batch-operations.json', logEntry);
        } catch (logError) {
            console.error('Failed to log batch results:', logError);
        }
    }
    
    // Content collection helper methods (simplified for now)
    async collectBrainstormingContent(projectId) { return ''; }
    async collectDiagrams(projectId) { return []; }
    async collectSpecifications(projectId) { return []; }
    async collectMilestones(projectId) { return []; }
    async collectTasks(projectId) { return []; }
    async collectSourceCode(projectId) { return {}; }
    async collectTests(projectId) { return {}; }
    async collectNotebooks(projectId) { return {}; }
    async collectDataSummary(projectId) { return ''; }
    async collectPaperContent(projectId) { return ''; }
    async collectFigures(projectId) { return []; }
    async collectBibliography(projectId) { return ''; }
}

export default AutomatedReviewManager;