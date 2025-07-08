/**
 * Pipeline Manager for llmXive Research Workflow
 * Manages the complete research pipeline from idea to publication
 */

class PipelineManager {
    constructor() {
        this.stageThresholds = {
            'idea': { minPoints: 0, nextStage: 'design', nextStatus: 'design' },
            'design': { minPoints: 3.0, nextStage: 'implementation_plan', nextStatus: 'planning' },
            'implementation_plan': { minPoints: 5.0, nextStage: 'in_progress', nextStatus: 'in_progress' },
            'in_progress': { minPoints: 80, nextStage: 'paper', nextStatus: 'review' }, // Based on completeness
            'paper': { minPoints: 5.0, nextStage: 'done', nextStatus: 'done' },
            'done': { minPoints: null, nextStage: null, nextStatus: null }
        };
        
        this.documentTemplates = {
            technicalDesign: this.getTechnicalDesignTemplate(),
            implementationPlan: this.getImplementationPlanTemplate(),
            latexPaper: this.getLatexPaperTemplate(),
            reviewTemplate: this.getReviewTemplate()
        };
    }

    /**
     * Check if project can advance and advance it if criteria are met
     */
    async checkAndAdvanceProject(projectId) {
        try {
            const project = window.ProjectDataManager.getProject(projectId);
            if (!project) {
                throw new Error('Project not found: ' + projectId);
            }

            const currentStage = project.phase || project.status;
            const threshold = this.stageThresholds[currentStage];
            
            if (!threshold || !threshold.nextStage) {
                console.log(`Project ${projectId} is at final stage: ${currentStage}`);
                return false;
            }

            // Calculate review points
            const reviewPoints = this.calculateReviewPoints(project);
            const completenessScore = project.completeness || 0;
            
            // Determine if advancement criteria are met
            let canAdvance = false;
            if (currentStage === 'in_progress') {
                // Use completeness score for implementation phase
                canAdvance = completenessScore >= threshold.minPoints;
            } else {
                // Use review points for other phases
                canAdvance = reviewPoints >= threshold.minPoints;
            }

            if (canAdvance) {
                await this.advanceProject(project, threshold.nextStage, threshold.nextStatus);
                return true;
            } else {
                console.log(`Project ${projectId} needs more points: ${reviewPoints}/${threshold.minPoints} (current: ${currentStage})`);
                return false;
            }
        } catch (error) {
            console.error('Error checking project advancement:', error);
            throw error;
        }
    }

    /**
     * Advance project to next stage
     */
    async advanceProject(project, nextPhase, nextStatus) {
        try {
            const updates = {
                phase: nextPhase,
                status: nextStatus,
                dateModified: new Date().toISOString().split('T')[0]
            };

            // Generate required documents for the new stage
            await this.generateStageDocuments(project, nextPhase);
            
            // Update project in database
            await window.ProjectDataManager.updateProject(project.id, updates);
            
            console.log(`✅ Advanced project ${project.id} to ${nextPhase}`);
            
            // Create advancement notification
            this.createAdvancementNotification(project, nextPhase);
            
        } catch (error) {
            console.error('Error advancing project:', error);
            throw error;
        }
    }

    /**
     * Calculate review points for a project
     */
    calculateReviewPoints(project) {
        if (!project.reviews || project.reviews.length === 0) {
            return 0;
        }

        let totalPoints = 0;
        project.reviews.forEach(review => {
            if (review.type === 'design' || review.type === 'automated') {
                totalPoints += 0.5; // LLM reviews worth 0.5 points
            } else if (review.type === 'manual' || review.type === 'human') {
                totalPoints += 1.0; // Human reviews worth 1.0 points
            }
        });

        return totalPoints;
    }

    /**
     * Generate documents required for each stage
     */
    async generateStageDocuments(project, stage) {
        try {
            switch (stage) {
                case 'design':
                    await this.generateTechnicalDesign(project);
                    break;
                case 'implementation_plan':
                    await this.generateImplementationPlan(project);
                    break;
                case 'in_progress':
                    await this.generateCodeStructure(project);
                    break;
                case 'paper':
                    await this.generateLatexPaper(project);
                    break;
                case 'done':
                    await this.generateFinalPDF(project);
                    break;
            }
        } catch (error) {
            console.error(`Error generating documents for stage ${stage}:`, error);
        }
    }

    /**
     * Generate technical design document
     */
    async generateTechnicalDesign(project) {
        const content = this.documentTemplates.technicalDesign
            .replace('{{PROJECT_TITLE}}', project.title)
            .replace('{{PROJECT_DESCRIPTION}}', project.description)
            .replace('{{PROJECT_FIELD}}', project.field)
            .replace('{{PROJECT_KEYWORDS}}', project.keywords ? project.keywords.join(', ') : '')
            .replace('{{DATE}}', new Date().toISOString().split('T')[0])
            .replace('{{CONTRIBUTORS}}', project.contributors.map(c => c.name).join(', '));

        // In a real implementation, this would write to the file system
        console.log(`📝 Generated technical design for ${project.id}`);
        
        // Store document reference in project
        const updates = {
            documents: {
                ...project.documents,
                technicalDesign: `technical_design_documents/${project.id}/design.md`
            }
        };
        
        return content;
    }

    /**
     * Generate implementation plan
     */
    async generateImplementationPlan(project) {
        const content = this.documentTemplates.implementationPlan
            .replace('{{PROJECT_TITLE}}', project.title)
            .replace('{{PROJECT_DESCRIPTION}}', project.description)
            .replace('{{TIMELINE}}', project.estimatedTimeline || '6-12 months')
            .replace('{{DATE}}', new Date().toISOString().split('T')[0]);

        console.log(`📋 Generated implementation plan for ${project.id}`);
        return content;
    }

    /**
     * Generate code structure
     */
    async generateCodeStructure(project) {
        // Create basic code structure based on project field
        const codeStructure = this.getCodeStructureTemplate(project.field);
        console.log(`💻 Generated code structure for ${project.id}`);
        return codeStructure;
    }

    /**
     * Generate LaTeX paper
     */
    async generateLatexPaper(project) {
        const content = this.documentTemplates.latexPaper
            .replace('{{PROJECT_TITLE}}', project.title)
            .replace('{{AUTHORS}}', project.contributors.map(c => c.name).join(', '))
            .replace('{{ABSTRACT}}', this.generateAbstract(project))
            .replace('{{INTRODUCTION}}', this.generateIntroduction(project))
            .replace('{{METHODS}}', this.generateMethods(project))
            .replace('{{DATE}}', new Date().toISOString().split('T')[0]);

        console.log(`📄 Generated LaTeX paper for ${project.id}`);
        return content;
    }

    /**
     * Generate final PDF
     */
    async generateFinalPDF(project) {
        // In a real implementation, this would compile LaTeX to PDF
        console.log(`📚 Generated final PDF for ${project.id}`);
        return true;
    }

    /**
     * Create advancement notification
     */
    createAdvancementNotification(project, newStage) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #10b981, #06b6d4);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 9999;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            max-width: 400px;
        `;
        
        notification.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 0.5rem;">🎉 Project Advanced!</div>
            <div>${project.title}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 0.25rem;">
                Advanced to: ${newStage.replace('_', ' ').toUpperCase()}
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    /**
     * Get technical design template
     */
    getTechnicalDesignTemplate() {
        return `# Technical Design Document

## Project: {{PROJECT_TITLE}}

**Field:** {{PROJECT_FIELD}}  
**Date:** {{DATE}}  
**Contributors:** {{CONTRIBUTORS}}

## Abstract

{{PROJECT_DESCRIPTION}}

## Keywords

{{PROJECT_KEYWORDS}}

## 1. Introduction

### 1.1 Problem Statement
[Describe the research problem and its significance]

### 1.2 Objectives
[List specific research objectives]

### 1.3 Scope
[Define the scope and limitations of the project]

## 2. Literature Review

### 2.1 Background
[Review relevant literature and previous work]

### 2.2 Gap Analysis
[Identify gaps in current knowledge]

## 3. Methodology

### 3.1 Approach
[Describe the overall methodological approach]

### 3.2 Data Requirements
[Specify data needs and sources]

### 3.3 Tools and Technologies
[List required tools and technologies]

## 4. Implementation Strategy

### 4.1 Phase Breakdown
[Break down implementation into phases]

### 4.2 Timeline
[Provide detailed timeline]

### 4.3 Resource Requirements
[Specify required resources]

## 5. Expected Outcomes

### 5.1 Deliverables
[List expected deliverables]

### 5.2 Success Metrics
[Define success criteria]

## 6. Risk Assessment

### 6.1 Technical Risks
[Identify potential technical challenges]

### 6.2 Mitigation Strategies
[Describe risk mitigation approaches]

## 7. References

[Add relevant references]

---
*Generated by llmXive Pipeline Manager*
`;
    }

    /**
     * Get implementation plan template
     */
    getImplementationPlanTemplate() {
        return `# Implementation Plan

## Project: {{PROJECT_TITLE}}

**Timeline:** {{TIMELINE}}  
**Date:** {{DATE}}

## Executive Summary

{{PROJECT_DESCRIPTION}}

## 1. Implementation Phases

### Phase 1: Setup and Planning (Weeks 1-2)
- [ ] Environment setup
- [ ] Data collection planning
- [ ] Tool selection and configuration

### Phase 2: Development (Weeks 3-8)
- [ ] Core implementation
- [ ] Data processing pipeline
- [ ] Initial testing

### Phase 3: Validation (Weeks 9-10)
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation

### Phase 4: Analysis (Weeks 11-12)
- [ ] Results analysis
- [ ] Report generation
- [ ] Peer review preparation

## 2. Milestones

| Milestone | Week | Deliverable |
|-----------|------|-------------|
| M1 | 2 | Setup Complete |
| M2 | 6 | Core Implementation |
| M3 | 10 | Validation Complete |
| M4 | 12 | Final Report |

## 3. Resource Allocation

### Human Resources
- Research Lead: 50% time
- Development Support: 25% time
- Data Analysis: 25% time

### Technical Resources
- Computing infrastructure
- Software licenses
- Data storage

## 4. Quality Assurance

### Testing Strategy
- Unit testing
- Integration testing
- Performance testing

### Review Process
- Weekly progress reviews
- Milestone gate reviews
- External peer review

## 5. Risk Management

### High-Priority Risks
1. Data availability delays
2. Technical implementation challenges
3. Resource constraints

### Mitigation Plans
[Detailed mitigation strategies for each risk]

---
*Generated by llmXive Pipeline Manager*
`;
    }

    /**
     * Get LaTeX paper template
     */
    getLatexPaperTemplate() {
        return `\\documentclass[11pt,a4paper]{article}
\\usepackage{amsmath,amsfonts,amssymb}
\\usepackage{graphicx}
\\usepackage{hyperref}
\\usepackage{natbib}

\\title{{{PROJECT_TITLE}}}
\\author{{{AUTHORS}}}
\\date{{{DATE}}}

\\begin{document}

\\maketitle

\\begin{abstract}
{{ABSTRACT}}
\\end{abstract}

\\section{Introduction}
{{INTRODUCTION}}

\\section{Methods}
{{METHODS}}

\\section{Results}
% Results section will be populated during implementation

\\section{Discussion}
% Discussion will be added based on results

\\section{Conclusion}
% Conclusions will be drawn from the analysis

\\section{Acknowledgments}
We acknowledge the llmXive platform for facilitating this research collaboration.

\\bibliographystyle{plain}
\\bibliography{references}

\\end{document}`;
    }

    /**
     * Get review template
     */
    getReviewTemplate() {
        return `# Review Template

## Project Information
- **Project ID:** {{PROJECT_ID}}
- **Title:** {{PROJECT_TITLE}}
- **Review Type:** {{REVIEW_TYPE}}
- **Reviewer:** {{REVIEWER}}
- **Date:** {{DATE}}

## Review Criteria

### Technical Merit (1-5)
- [ ] 1 - Poor
- [ ] 2 - Below Average
- [ ] 3 - Average
- [ ] 4 - Good
- [ ] 5 - Excellent

### Novelty (1-5)
- [ ] 1 - Not Novel
- [ ] 2 - Limited Novelty
- [ ] 3 - Moderate Novelty
- [ ] 4 - Novel
- [ ] 5 - Highly Novel

### Feasibility (1-5)
- [ ] 1 - Not Feasible
- [ ] 2 - Low Feasibility
- [ ] 3 - Moderate Feasibility
- [ ] 4 - Feasible
- [ ] 5 - Highly Feasible

## Detailed Comments

### Strengths
[List project strengths]

### Weaknesses
[List areas for improvement]

### Recommendations
[Provide specific recommendations]

## Decision
- [ ] Accept as-is
- [ ] Accept with minor revisions
- [ ] Accept with major revisions
- [ ] Reject

## Review Score: __/5

---
*llmXive Review System*
`;
    }

    /**
     * Generate project-specific content
     */
    generateAbstract(project) {
        return `This study presents ${project.title.toLowerCase()}, a ${project.field.toLowerCase()} research project focused on ${project.description.toLowerCase()}. The research addresses key challenges in the field and proposes innovative solutions to advance current understanding.`;
    }

    generateIntroduction(project) {
        return `The field of ${project.field.toLowerCase()} has seen significant advances in recent years. This project, titled "${project.title}", aims to contribute to this growing body of knowledge by investigating ${project.description.toLowerCase()}. The research is motivated by the need to address current limitations and explore new methodological approaches.`;
    }

    generateMethods(project) {
        return `This study employs a comprehensive methodological approach suitable for ${project.field.toLowerCase()} research. The methodology includes data collection, analysis protocols, and validation procedures designed to ensure robust and reproducible results.`;
    }

    /**
     * Get code structure based on project field
     */
    getCodeStructureTemplate(field) {
        const templates = {
            'Biology': {
                'src/': ['analysis.py', 'visualization.py', 'data_processing.py'],
                'data/': ['raw/', 'processed/', 'results/'],
                'notebooks/': ['exploratory_analysis.ipynb', 'results_visualization.ipynb'],
                'tests/': ['test_analysis.py', 'test_processing.py'],
                'requirements.txt': 'numpy\npandas\nscipy\nmatplotlib\nseaborn\nbiopython'
            },
            'Computer Science': {
                'src/': ['main.py', 'models.py', 'utils.py', 'config.py'],
                'data/': ['datasets/', 'models/', 'outputs/'],
                'notebooks/': ['experiments.ipynb', 'evaluation.ipynb'],
                'tests/': ['test_models.py', 'test_utils.py'],
                'requirements.txt': 'torch\nnumpy\nscikit-learn\nmatplotlib\njupyter'
            },
            'default': {
                'src/': ['main.py', 'analysis.py', 'utils.py'],
                'data/': ['input/', 'output/'],
                'notebooks/': ['analysis.ipynb'],
                'tests/': ['test_main.py'],
                'requirements.txt': 'numpy\npandas\nmatplotlib\njupyter'
            }
        };

        return templates[field] || templates['default'];
    }
}

// Create global instance
window.PipelineManager = new PipelineManager();

console.log('🔄 PipelineManager loaded');