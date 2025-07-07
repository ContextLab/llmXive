/**
 * ModerationManager - Content moderation and security features
 * 
 * Handles automated content scanning, user management, and security
 * for the llmXive system.
 */

class ModerationManager {
    constructor(fileManager, systemConfig, modelManager) {
        this.fileManager = fileManager;
        this.systemConfig = systemConfig;
        this.modelManager = modelManager;
        
        this.usersPath = '.llmxive-system/registry/users.json';
        this.moderationLogPath = '.llmxive-system/logs/moderation.json';
        
        // Moderation rules and patterns
        this.blockedPatterns = new Set();
        this.suspiciousPatterns = new Set();
        this.initializeModerationRules();
    }
    
    /**
     * Initialize moderation rules and patterns
     */
    initializeModerationRules() {
        // Blocked content patterns
        this.blockedPatterns.add(/\b(spam|scam|phishing)\b/i);
        this.blockedPatterns.add(/\b(hack|exploit|malware)\b/i);
        this.blockedPatterns.add(/\b(password|api[_\s]?key|secret)\s*[:=]\s*\S+/i);
        this.blockedPatterns.add(/(https?:\/\/[^\s]+\.(tk|ml|ga|cf))/i); // Suspicious domains
        
        // Suspicious patterns (require review)
        this.suspiciousPatterns.add(/\b(cryptocurrency|bitcoin|trading)\b/i);
        this.suspiciousPatterns.add(/\b(urgent|immediate|limited[_\s]?time)\b/i);
        this.suspiciousPatterns.add(/\b(contact[_\s]?me|dm[_\s]?me|email[_\s]?me)\b/i);
        this.suspiciousPatterns.add(/[A-Z]{10,}/); // Excessive caps
    }
    
    /**
     * Moderate project content
     */
    async moderateProject(projectId) {
        try {
            console.log(`Starting moderation for project: ${projectId}`);
            
            // Get project data
            const project = await this.getProjectForModeration(projectId);
            if (!project) {
                throw new Error(`Project not found: ${projectId}`);
            }
            
            // Check user reputation
            const userStatus = await this.checkUserStatus(project.creator);
            if (userStatus.blocked) {
                return this.createModerationResult(projectId, 'blocked', 'User is blocked', {
                    action: 'block_project',
                    reason: 'blocked_user'
                });
            }
            
            // Collect all text content from project
            const content = await this.collectProjectContent(projectId);
            
            // Run automated moderation checks
            const automatedResult = await this.runAutomatedModeration(content);
            
            // Run AI-powered moderation if needed
            let aiResult = null;
            if (automatedResult.requiresAIReview || userStatus.suspicious) {
                aiResult = await this.runAIModerationCheck(content);
            }
            
            // Determine final moderation decision
            const decision = this.makeModerationDecision(automatedResult, aiResult, userStatus);
            
            // Log moderation result
            await this.logModerationResult(projectId, project.creator, decision);
            
            // Take action based on decision
            await this.executeModerationAction(projectId, decision);
            
            console.log(`Moderation completed for ${projectId}: ${decision.status}`);
            
            return decision;
            
        } catch (error) {
            console.error(`Moderation failed for ${projectId}:`, error);
            
            // Log moderation error
            await this.logModerationError(projectId, error.message);
            
            throw error;
        }
    }
    
    /**
     * Get project data for moderation
     */
    async getProjectForModeration(projectId) {
        try {
            const config = await this.fileManager.readJSON(`projects/${projectId}/.llmxive/config.json`);
            
            if (!config) {
                return null;
            }
            
            return {
                id: projectId,
                title: config.project.title,
                description: config.project.description,
                creator: config.contributors[0]?.name || 'unknown',
                createdDate: config.project.created_date,
                status: config.project.status
            };
            
        } catch (error) {
            console.error(`Failed to get project for moderation: ${projectId}`, error);
            return null;
        }
    }
    
    /**
     * Check user status and reputation
     */
    async checkUserStatus(username) {
        try {
            const users = await this.fileManager.readJSON(this.usersPath);
            
            if (!users || !users.users[username]) {
                // New user - neutral status
                return {
                    blocked: false,
                    suspicious: false,
                    trusted: false,
                    reputation: 0
                };
            }
            
            const user = users.users[username];
            
            return {
                blocked: users.moderation.blocked_users.includes(username),
                suspicious: users.moderation.warning_users.includes(username),
                trusted: users.moderation.trusted_users.includes(username),
                reputation: user.reputation || 0,
                violationCount: user.violation_count || 0
            };
            
        } catch (error) {
            console.error(`Failed to check user status for ${username}:`, error);
            return { blocked: false, suspicious: false, trusted: false, reputation: 0 };
        }
    }
    
    /**
     * Collect all text content from project
     */
    async collectProjectContent(projectId) {
        const content = {};
        
        try {
            // Project metadata
            const config = await this.fileManager.readJSON(`projects/${projectId}/.llmxive/config.json`);
            if (config) {
                content.title = config.project.title;
                content.description = config.project.description;
            }
            
            // Idea content
            const idea = await this.readTextFile(`projects/${projectId}/idea/initial-idea.md`);
            if (idea) content.idea = idea;
            
            // Technical design
            const design = await this.readTextFile(`projects/${projectId}/technical-design/main.md`);
            if (design) content.design = design;
            
            // Implementation plan
            const plan = await this.readTextFile(`projects/${projectId}/implementation-plan/main.md`);
            if (plan) content.plan = plan;
            
            // README
            const readme = await this.readTextFile(`projects/${projectId}/README.md`);
            if (readme) content.readme = readme;
            
            // Collect any additional .md files
            const additionalFiles = await this.collectAdditionalTextFiles(projectId);
            Object.assign(content, additionalFiles);
            
            return content;
            
        } catch (error) {
            console.error(`Failed to collect project content for ${projectId}:`, error);
            return content;
        }
    }
    
    /**
     * Read text file with error handling
     */
    async readTextFile(filePath) {
        try {
            const content = await this.fileManager.readJSON(filePath);
            return typeof content === 'string' ? content : JSON.stringify(content);
        } catch (error) {
            return null;
        }
    }
    
    /**
     * Collect additional text files from project
     */
    async collectAdditionalTextFiles(projectId) {
        // For now, return empty object
        // In a full implementation, this would scan for .md, .txt files
        return {};
    }
    
    /**
     * Run automated pattern-based moderation
     */
    async runAutomatedModeration(content) {
        const result = {
            blocked: false,
            suspicious: false,
            requiresAIReview: false,
            violations: [],
            warnings: [],
            score: 0
        };
        
        // Combine all content for analysis
        const allText = Object.values(content).join(' ').toLowerCase();
        
        // Check for blocked patterns
        for (const pattern of this.blockedPatterns) {
            if (pattern.test(allText)) {
                result.blocked = true;
                result.violations.push({
                    type: 'blocked_pattern',
                    pattern: pattern.source,
                    severity: 'high'
                });
            }
        }
        
        // Check for suspicious patterns
        for (const pattern of this.suspiciousPatterns) {
            if (pattern.test(allText)) {
                result.suspicious = true;
                result.warnings.push({
                    type: 'suspicious_pattern',
                    pattern: pattern.source,
                    severity: 'medium'
                });
            }
        }
        
        // Additional checks
        if (this.hasExcessiveLinks(allText)) {
            result.suspicious = true;
            result.warnings.push({
                type: 'excessive_links',
                severity: 'medium'
            });
        }
        
        if (this.hasLowQualityIndicators(allText)) {
            result.requiresAIReview = true;
            result.warnings.push({
                type: 'low_quality_content',
                severity: 'low'
            });
        }
        
        // Calculate risk score
        result.score = this.calculateRiskScore(result);
        
        // Determine if AI review is needed
        if (result.score > 0.3 || result.suspicious) {
            result.requiresAIReview = true;
        }
        
        return result;
    }
    
    /**
     * Check for excessive links
     */
    hasExcessiveLinks(text) {
        const linkPattern = /https?:\/\/[^\s]+/g;
        const links = text.match(linkPattern) || [];
        return links.length > 5; // More than 5 links is suspicious
    }
    
    /**
     * Check for low quality indicators
     */
    hasLowQualityIndicators(text) {
        // Very short content
        if (text.length < 100) {
            return true;
        }
        
        // Excessive repetition
        const words = text.split(' ');
        const uniqueWords = new Set(words);
        if (words.length > 20 && uniqueWords.size / words.length < 0.3) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Calculate risk score based on violations and warnings
     */
    calculateRiskScore(result) {
        let score = 0;
        
        // High severity violations
        score += result.violations.filter(v => v.severity === 'high').length * 0.5;
        
        // Medium severity warnings
        score += result.warnings.filter(w => w.severity === 'medium').length * 0.2;
        
        // Low severity warnings
        score += result.warnings.filter(w => w.severity === 'low').length * 0.1;
        
        return Math.min(score, 1.0); // Cap at 1.0
    }
    
    /**
     * Run AI-powered moderation check
     */
    async runAIModerationCheck(content) {
        try {
            console.log('Running AI moderation check...');
            
            // Prepare content for AI analysis
            const contentSummary = this.prepareContentForAI(content);
            
            // Create moderation prompt
            const prompt = this.createModerationPrompt(contentSummary);
            
            // Select appropriate model for moderation
            const model = await this.modelManager.selectModelForTask('content_moderation', {
                minQuality: 0.8,
                maxCost: 0.01 // Keep costs low for moderation
            });
            
            // Execute model call
            const response = await this.modelManager.executeModelCall(
                model.id,
                prompt,
                {
                    maxTokens: 300,
                    temperature: 0.1
                }
            );
            
            // Parse AI response
            const aiResult = this.parseAIModerationResponse(response.response.content);
            
            console.log(`AI moderation completed with confidence: ${aiResult.confidence}`);
            
            return aiResult;
            
        } catch (error) {
            console.error('AI moderation check failed:', error);
            
            // Return safe default
            return {
                safe: true,
                confidence: 0.5,
                reasoning: 'AI moderation failed, defaulting to safe',
                concerns: []
            };
        }
    }
    
    /**
     * Prepare content for AI analysis
     */
    prepareContentForAI(content) {
        // Combine and truncate content for AI analysis
        const combined = Object.entries(content)
            .map(([key, value]) => `${key}: ${value}`)
            .join('\n\n');
        
        // Limit to 2000 characters to manage token usage
        return combined.length > 2000 ? combined.substring(0, 2000) + '...' : combined;
    }
    
    /**
     * Create moderation prompt for AI
     */
    createModerationPrompt(content) {
        return `You are a content moderator for an academic research platform. Please analyze the following project content for potential policy violations, spam, or inappropriate material.

Content to analyze:
${content}

Please evaluate for:
1. Spam or promotional content
2. Inappropriate or offensive material  
3. Security risks (exposed credentials, malicious links)
4. Academic integrity concerns
5. Overall content quality

Respond with a JSON object:
{
  "safe": true/false,
  "confidence": 0.0-1.0,
  "concerns": ["concern1", "concern2"],
  "reasoning": "Brief explanation",
  "recommended_action": "approve/review/reject"
}`;
    }
    
    /**
     * Parse AI moderation response
     */
    parseAIModerationResponse(responseText) {
        try {
            // Try to extract JSON from response
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const result = JSON.parse(jsonMatch[0]);
                
                // Validate structure
                if (typeof result.safe === 'boolean' && typeof result.confidence === 'number') {
                    return result;
                }
            }
            
            // Fallback parsing
            const safe = !responseText.toLowerCase().includes('unsafe') && 
                        !responseText.toLowerCase().includes('violation');
            
            return {
                safe: safe,
                confidence: 0.6,
                reasoning: 'Parsed from text response',
                concerns: safe ? [] : ['Potential policy violation detected'],
                recommended_action: safe ? 'approve' : 'review'
            };
            
        } catch (error) {
            console.error('Failed to parse AI moderation response:', error);
            
            // Safe default
            return {
                safe: true,
                confidence: 0.3,
                reasoning: 'Failed to parse AI response, defaulting to safe',
                concerns: [],
                recommended_action: 'review'
            };
        }
    }
    
    /**
     * Make final moderation decision
     */
    makeModerationDecision(automatedResult, aiResult, userStatus) {
        // Immediate block for high-risk content
        if (automatedResult.blocked) {
            return this.createModerationResult(null, 'blocked', 'Automated violation detected', {
                action: 'block_project',
                reason: 'policy_violation',
                details: automatedResult.violations
            });
        }
        
        // Block if AI determines unsafe with high confidence
        if (aiResult && !aiResult.safe && aiResult.confidence > 0.8) {
            return this.createModerationResult(null, 'blocked', 'AI moderation flagged unsafe content', {
                action: 'block_project',
                reason: 'ai_safety_violation',
                details: aiResult.concerns
            });
        }
        
        // Require manual review for suspicious content
        if (automatedResult.suspicious || (aiResult && !aiResult.safe) || userStatus.suspicious) {
            return this.createModerationResult(null, 'review_required', 'Content requires manual review', {
                action: 'require_manual_review',
                reason: 'suspicious_content',
                priority: this.calculateReviewPriority(automatedResult, aiResult, userStatus)
            });
        }
        
        // Approve for trusted users or clean content
        if (userStatus.trusted || (automatedResult.score < 0.1 && (!aiResult || aiResult.safe))) {
            return this.createModerationResult(null, 'approved', 'Content approved', {
                action: 'approve',
                reason: 'clean_content'
            });
        }
        
        // Default to manual review
        return this.createModerationResult(null, 'review_required', 'Default manual review', {
            action: 'require_manual_review',
            reason: 'default_review',
            priority: 'low'
        });
    }
    
    /**
     * Create standardized moderation result
     */
    createModerationResult(projectId, status, message, action) {
        return {
            projectId: projectId,
            status: status, // 'approved', 'blocked', 'review_required'
            message: message,
            action: action,
            timestamp: new Date().toISOString(),
            moderatedBy: 'automated_system'
        };
    }
    
    /**
     * Calculate review priority
     */
    calculateReviewPriority(automatedResult, aiResult, userStatus) {
        let score = 0;
        
        if (automatedResult.score > 0.5) score += 2;
        if (aiResult && !aiResult.safe && aiResult.confidence > 0.6) score += 2;
        if (userStatus.suspicious) score += 1;
        if (userStatus.violationCount > 0) score += 1;
        
        if (score >= 4) return 'high';
        if (score >= 2) return 'medium';
        return 'low';
    }
    
    /**
     * Execute moderation action
     */
    async executeModerationAction(projectId, decision) {
        try {
            switch (decision.action.action) {
                case 'block_project':
                    await this.blockProject(projectId, decision);
                    break;
                    
                case 'require_manual_review':
                    await this.createReviewIssue(projectId, decision);
                    break;
                    
                case 'approve':
                    // No action needed for approval
                    break;
                    
                default:
                    console.warn(`Unknown moderation action: ${decision.action.action}`);
            }
            
        } catch (error) {
            console.error(`Failed to execute moderation action for ${projectId}:`, error);
        }
    }
    
    /**
     * Block project by updating its status
     */
    async blockProject(projectId, decision) {
        try {
            const config = await this.fileManager.readJSON(`projects/${projectId}/.llmxive/config.json`);
            if (config) {
                config.project.status = 'blocked';
                config.project.blocked_reason = decision.message;
                config.project.blocked_date = new Date().toISOString();
                
                await this.fileManager.writeJSON(
                    `projects/${projectId}/.llmxive/config.json`,
                    config,
                    `Block project: ${decision.message}`
                );
            }
            
        } catch (error) {
            console.error(`Failed to block project ${projectId}:`, error);
        }
    }
    
    /**
     * Create GitHub issue for manual review
     */
    async createReviewIssue(projectId, decision) {
        // This would create a GitHub issue for manual review
        // For now, just log the need for review
        
        await this.fileManager.appendToLog('.llmxive-system/logs/manual-reviews-needed.json', {
            type: 'manual_review_needed',
            projectId: projectId,
            reason: decision.action.reason,
            priority: decision.action.priority,
            details: decision.message,
            timestamp: new Date().toISOString()
        });
    }
    
    /**
     * Log moderation result
     */
    async logModerationResult(projectId, creator, decision) {
        const logEntry = {
            type: 'moderation_result',
            projectId: projectId,
            creator: creator,
            status: decision.status,
            action: decision.action.action,
            reason: decision.action.reason,
            timestamp: decision.timestamp
        };
        
        try {
            await this.fileManager.appendToLog(this.moderationLogPath, logEntry);
        } catch (error) {
            console.error('Failed to log moderation result:', error);
        }
    }
    
    /**
     * Log moderation error
     */
    async logModerationError(projectId, errorMessage) {
        const logEntry = {
            type: 'moderation_error',
            projectId: projectId,
            error: errorMessage,
            timestamp: new Date().toISOString()
        };
        
        try {
            await this.fileManager.appendToLog(this.moderationLogPath, logEntry);
        } catch (error) {
            console.error('Failed to log moderation error:', error);
        }
    }
    
    /**
     * Get moderation statistics
     */
    async getModerationStatistics() {
        try {
            const logs = await this.fileManager.readJSON(this.moderationLogPath);
            if (!logs || !logs.entries) {
                return { total: 0, approved: 0, blocked: 0, reviewRequired: 0 };
            }
            
            const entries = logs.entries.filter(entry => entry.type === 'moderation_result');
            
            return {
                total: entries.length,
                approved: entries.filter(e => e.status === 'approved').length,
                blocked: entries.filter(e => e.status === 'blocked').length,
                reviewRequired: entries.filter(e => e.status === 'review_required').length,
                last30Days: entries.filter(e => {
                    const entryDate = new Date(e.timestamp);
                    const thirtyDaysAgo = new Date();
                    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
                    return entryDate > thirtyDaysAgo;
                }).length
            };
            
        } catch (error) {
            console.error('Failed to get moderation statistics:', error);
            return { total: 0, approved: 0, blocked: 0, reviewRequired: 0 };
        }
    }
}

export default ModerationManager;