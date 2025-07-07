#!/usr/bin/env node

/**
 * Generate Automated Reviews Script
 * 
 * This script runs in GitHub Actions to generate automated reviews
 * for eligible projects using AI models.
 */

import UnifiedGitHubClient from '../src/core/UnifiedGitHubClient.js';

// Mock GitHub API for Actions environment
class GitHubActionsAPI {
    constructor() {
        this.token = process.env.GITHUB_TOKEN;
        this.repo = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'llmXive';
        this.owner = process.env.GITHUB_REPOSITORY?.split('/')[0] || 'ContextLab';
    }
    
    rest = {
        repos: {
            getContent: async (params) => {
                const { spawn } = await import('child_process');
                const { promisify } = await import('util');
                const execAsync = promisify(spawn);
                
                try {
                    // Use git to read file content
                    const result = await execAsync('cat', [params.path], { encoding: 'utf8' });
                    const content = Buffer.from(result.stdout).toString('base64');
                    
                    return {
                        data: {
                            type: 'file',
                            content: content,
                            sha: 'mock-sha'
                        }
                    };
                } catch (error) {
                    const gitError = new Error('File not found');
                    gitError.status = 404;
                    throw gitError;
                }
            },
            
            createOrUpdateFileContents: async (params) => {
                const fs = await import('fs');
                const path = await import('path');
                
                // Decode base64 content
                const content = Buffer.from(params.content, 'base64').toString('utf8');
                
                // Ensure directory exists
                const dir = path.dirname(params.path);
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                
                // Write file
                fs.writeFileSync(params.path, content);
                
                return {
                    data: {
                        content: {
                            sha: 'new-sha',
                            path: params.path
                        },
                        commit: {
                            sha: 'commit-sha',
                            message: params.message
                        }
                    }
                };
            }
        }
    };
}

async function main() {
    try {
        console.log('🤖 Starting automated review generation...');
        
        // Initialize client with Actions-specific configuration
        const client = new UnifiedGitHubClient({
            owner: process.env.GITHUB_REPOSITORY?.split('/')[0] || 'ContextLab',
            repo: process.env.GITHUB_REPOSITORY?.split('/')[1] || 'llmXive',
            branch: process.env.GITHUB_REF_NAME || 'main'
        });
        
        // Mock authentication for Actions environment
        client.auth.token = process.env.GITHUB_TOKEN;
        client.auth.user = { login: 'github-actions[bot]', name: 'GitHub Actions' };
        client.auth.permissions = { admin: true, push: true, pull: true };
        
        // Use Actions-specific GitHub API
        client.github = new GitHubActionsAPI();
        
        // Initialize file manager with Actions API
        const { default: FileManager } = await import('../src/core/FileManager.js');
        client.fileManager = new FileManager(client.github, {
            owner: client.options.owner,
            repo: client.options.repo,
            branch: client.options.branch
        });
        
        // Initialize system config
        const { default: SystemConfig } = await import('../src/core/SystemConfig.js');
        client.systemConfig = new SystemConfig(client.fileManager);
        
        // Check if system is initialized
        const systemInitialized = await client.systemConfig.isInitialized();
        if (!systemInitialized) {
            console.log('System not initialized, skipping automated reviews');
            process.exit(0);
        }
        
        // Initialize managers
        const { default: ProjectManager } = await import('../src/managers/ProjectManager.js');
        const { default: ReviewManager } = await import('../src/managers/ReviewManager.js');
        const { default: ModelManager } = await import('../src/managers/ModelManager.js');
        const { default: AutomatedReviewManager } = await import('../src/managers/AutomatedReviewManager.js');
        
        client.projectManager = new ProjectManager(client.fileManager, client.systemConfig);
        client.reviewManager = new ReviewManager(client.fileManager, client.systemConfig, client.projectManager);
        client.modelManager = new ModelManager(client.fileManager, client.systemConfig);
        client.automatedReviewManager = new AutomatedReviewManager(
            client.fileManager,
            client.systemConfig,
            client.projectManager,
            client.reviewManager,
            client.modelManager
        );
        
        // Initialize model manager
        await client.modelManager.initialize();
        
        // Check for specific project ID from workflow input
        const projectId = process.env.PROJECT_ID;
        const forceReview = process.env.FORCE_REVIEW === 'true';
        
        let result;
        
        if (projectId) {
            console.log(`🎯 Generating reviews for specific project: ${projectId}`);
            
            // Generate reviews for specific project
            const project = await client.projectManager.getProject(projectId);
            if (!project) {
                throw new Error(`Project not found: ${projectId}`);
            }
            
            const reviewsGenerated = [];
            const errors = [];
            
            for (const [phaseId, phase] of Object.entries(project.phases)) {
                if (phase.status !== 'pending') {
                    const reviewTypes = client.automatedReviewManager.getRequiredReviewTypes(phaseId);
                    
                    for (const reviewType of reviewTypes) {
                        try {
                            const reviewResult = await client.automatedReviewManager.generateAutomatedReview(
                                projectId,
                                phaseId,
                                reviewType
                            );
                            
                            reviewsGenerated.push({
                                projectId,
                                phase: phaseId,
                                reviewType,
                                reviewId: reviewResult.reviewId,
                                model: reviewResult.model,
                                points: reviewResult.points
                            });
                            
                        } catch (error) {
                            errors.push({
                                projectId,
                                phase: phaseId,
                                reviewType,
                                error: error.message
                            });
                        }
                    }
                }
            }
            
            result = {
                success: true,
                reviewsGenerated: reviewsGenerated.length,
                errors: errors.length,
                details: { reviewsGenerated, errors }
            };
            
        } else {
            console.log('🔄 Generating batch reviews for all eligible projects...');
            
            // Generate batch reviews for all projects
            const options = {
                minTimeBetweenReviews: forceReview ? 0 : 24 * 60 * 60 * 1000, // 24 hours unless forced
                maxReviewsPerRun: 50 // Limit to prevent overwhelming the system
            };
            
            result = await client.automatedReviewManager.generateBatchReviews(options);
        }
        
        // Output results
        console.log(`✅ Review generation completed:`);
        console.log(`   - Reviews generated: ${result.reviewsGenerated}`);
        console.log(`   - Errors encountered: ${result.errors}`);
        
        if (result.details?.reviewsGenerated) {
            console.log('\n📝 Generated Reviews:');
            result.details.reviewsGenerated.forEach(review => {
                console.log(`   - ${review.projectId}/${review.phase}: ${review.reviewType} (${review.points} points, ${review.model})`);
            });
        }
        
        if (result.details?.errors && result.details.errors.length > 0) {
            console.log('\n❌ Errors:');
            result.details.errors.forEach(error => {
                console.log(`   - ${error.projectId}/${error.phase}: ${error.error}`);
            });
        }
        
        // Set output for workflow
        console.log(`\n::set-output name=reviews_generated::${result.reviewsGenerated}`);
        console.log(`::set-output name=errors::${result.errors}`);
        
        process.exit(result.errors > 0 ? 1 : 0);
        
    } catch (error) {
        console.error('❌ Automated review generation failed:', error);
        console.error(error.stack);
        process.exit(1);
    }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}