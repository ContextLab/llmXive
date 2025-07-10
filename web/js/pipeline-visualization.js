/**
 * Pipeline Visualization Component
 * Generates dynamic flowchart from YAML configuration
 */

class PipelineVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentConfig = null;
        this.mermaidInitialized = false;
        
        this.init();
    }
    
    async init() {
        await this.loadConfiguration();
        this.setupContainer();
        await this.renderVisualization();
        this.setupEventListeners();
    }
    
    async loadConfiguration() {
        try {
            const response = await fetch('/api/pipeline/config');
            if (response.ok) {
                const yamlContent = await response.text();
                this.currentConfig = this.parseYAML(yamlContent);
            } else {
                console.error('Failed to load pipeline configuration');
                this.currentConfig = this.getDefaultConfig();
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.currentConfig = this.getDefaultConfig();
        }
    }
    
    setupContainer() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="pipeline-visualization">
                <div class="visualization-header">
                    <h3>🔄 Research Pipeline Flow</h3>
                    <div class="visualization-controls">
                        <button id="refresh-pipeline-viz" class="btn btn-sm btn-secondary">
                            🔄 Refresh
                        </button>
                        <button id="expand-pipeline-viz" class="btn btn-sm btn-info">
                            🔍 Expand
                        </button>
                        ${this.isAdmin() ? `
                        <button id="edit-pipeline-config" class="btn btn-sm btn-primary">
                            ✏️ Edit
                        </button>
                        ` : ''}
                    </div>
                </div>
                
                <div class="visualization-content">
                    <div id="pipeline-flowchart" class="flowchart-display"></div>
                    
                    <div class="pipeline-legend">
                        <h4>Legend</h4>
                        <div class="legend-items">
                            <div class="legend-item">
                                <span class="legend-color step-idea"></span>
                                <span>Idea Generation</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color step-design"></span>
                                <span>Design & Planning</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color step-execution"></span>
                                <span>Code & Execution</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color step-analysis"></span>
                                <span>Analysis & Review</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color step-publication"></span>
                                <span>Publication</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="pipeline-stats">
                    <div class="stat-item">
                        <span class="stat-value" id="total-steps">-</span>
                        <span class="stat-label">Total Steps</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="parallel-steps">-</span>
                        <span class="stat-label">Parallel Capable</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="review-steps">-</span>
                        <span class="stat-label">Review Steps</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="estimated-time">-</span>
                        <span class="stat-label">Est. Duration</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    async renderVisualization() {
        const flowchartContainer = document.getElementById('pipeline-flowchart');
        if (!flowchartContainer || !this.currentConfig) return;
        
        try {
            const mermaidCode = this.generateMermaidDiagram();
            
            // Initialize Mermaid if not already done
            if (typeof mermaid !== 'undefined' && !this.mermaidInitialized) {
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    flowchart: {
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    }
                });
                this.mermaidInitialized = true;
            }
            
            if (typeof mermaid !== 'undefined') {
                // Clear previous content
                flowchartContainer.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
                
                // Render the diagram
                await mermaid.init(undefined, flowchartContainer.querySelector('.mermaid'));
                
                // Add interactive elements
                this.addInteractivity();
            } else {
                // Fallback display
                flowchartContainer.innerHTML = `
                    <div class="flowchart-fallback">
                        <h4>Pipeline Steps</h4>
                        <div class="step-list">
                            ${this.generateStepList()}
                        </div>
                    </div>
                `;
            }
            
            // Update statistics
            this.updateStatistics();
            
        } catch (error) {
            console.error('Error rendering visualization:', error);
            flowchartContainer.innerHTML = `
                <div class="visualization-error">
                    <p>Unable to render pipeline visualization</p>
                    <details>
                        <summary>Error Details</summary>
                        <pre>${error.message}</pre>
                    </details>
                </div>
            `;
        }
    }
    
    generateMermaidDiagram() {
        const steps = this.currentConfig.steps || {};
        const branches = this.currentConfig.branches || {};
        
        let mermaid = 'graph TD\n';
        
        // Define step categories for styling
        const stepCategories = {
            idea: ['idea_generation', 'idea_review', 'idea_revision'],
            design: ['technical_design', 'design_review', 'implementation_plan'],
            execution: ['code_generation', 'code_execution'],
            analysis: ['data_analysis', 'paper_writing', 'paper_review'],
            publication: ['latex_compilation']
        };
        
        // Add nodes with styling
        Object.entries(steps).forEach(([stepName, step]) => {
            const category = this.getStepCategory(stepName, stepCategories);
            const label = this.formatStepLabel(step.description || stepName);
            const timeout = step.timeout || 300;
            
            mermaid += `    ${stepName}["${label}<br/><small>${timeout}s</small>"]\n`;
            mermaid += `    class ${stepName} ${category}\n`;
        });
        
        // Add dependencies
        Object.entries(steps).forEach(([stepName, step]) => {
            const dependencies = step.depends_on || [];
            dependencies.forEach(dep => {
                if (steps[dep]) {
                    mermaid += `    ${dep} --> ${stepName}\n`;
                }
            });
        });
        
        // Add conditional branches
        Object.entries(branches).forEach(([branchName, branch]) => {
            const condition = this.formatCondition(branch.condition);
            mermaid += `    ${branchName}{{"${condition}"}}\n`;
            mermaid += `    class ${branchName} branch\n`;
        });
        
        // Add styling classes
        mermaid += this.getMermaidStyling();
        
        return mermaid;
    }
    
    getStepCategory(stepName, categories) {
        for (const [category, steps] of Object.entries(categories)) {
            if (steps.includes(stepName)) {
                return `step-${category}`;
            }
        }
        return 'step-default';
    }
    
    formatStepLabel(description) {
        // Truncate and clean description for display
        const maxLength = 30;
        let label = description.replace(/[^a-zA-Z0-9\s]/g, '');
        if (label.length > maxLength) {
            label = label.substring(0, maxLength) + '...';
        }
        return label;
    }
    
    formatCondition(condition) {
        // Simplify condition for display
        return condition.length > 20 ? condition.substring(0, 20) + '...' : condition;
    }
    
    getMermaidStyling() {
        return `
    classDef step-idea fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef step-design fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef step-execution fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef step-analysis fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef step-publication fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef branch fill:#fff9c4,stroke:#f9a825,stroke-width:2px
    classDef step-default fill:#f5f5f5,stroke:#757575,stroke-width:2px
        `;
    }
    
    generateStepList() {
        const steps = this.currentConfig.steps || {};
        return Object.entries(steps).map(([stepName, step]) => `
            <div class="step-item">
                <h5>${stepName}</h5>
                <p>${step.description}</p>
                <div class="step-meta">
                    <span>⏱️ ${step.timeout || 300}s</span>
                    <span>🔗 ${(step.depends_on || []).length} deps</span>
                </div>
            </div>
        `).join('');
    }
    
    addInteractivity() {
        // Add click handlers to steps for more information
        const stepNodes = document.querySelectorAll('#pipeline-flowchart .node');
        stepNodes.forEach(node => {
            node.style.cursor = 'pointer';
            node.addEventListener('click', (e) => {
                const stepId = this.extractStepId(node);
                if (stepId) {
                    this.showStepDetails(stepId);
                }
            });
        });
    }
    
    extractStepId(node) {
        // Extract step ID from Mermaid node
        const textElement = node.querySelector('span');
        if (textElement) {
            const text = textElement.textContent;
            // This is a simplified extraction - may need refinement
            return text.split(':')[0]?.trim();
        }
        return null;
    }
    
    showStepDetails(stepId) {
        const step = this.currentConfig.steps?.[stepId];
        if (!step) return;
        
        // Create modal or tooltip with step details
        const modal = document.createElement('div');
        modal.className = 'step-details-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h4>${stepId}</h4>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>Description:</strong> ${step.description}</p>
                    <p><strong>Dependencies:</strong> ${(step.depends_on || []).join(', ') || 'None'}</p>
                    <p><strong>Timeout:</strong> ${step.timeout || 300} seconds</p>
                    <p><strong>Model Requirements:</strong> ${this.formatModelRequirements(step.model_selection)}</p>
                    <p><strong>Inputs:</strong> ${(step.inputs || []).join(', ') || 'None'}</p>
                    <p><strong>Outputs:</strong> ${(step.outputs || []).join(', ') || 'None'}</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close modal handlers
        modal.querySelector('.close-modal').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }
    
    formatModelRequirements(modelSelection) {
        if (!modelSelection) return 'Not specified';
        
        const parts = [];
        if (modelSelection.min_parameters) {
            parts.push(`Min ${modelSelection.min_parameters}B params`);
        }
        if (modelSelection.preferred_models) {
            parts.push(`Prefers: ${modelSelection.preferred_models.join(', ')}`);
        }
        
        return parts.join(', ') || 'Any available model';
    }
    
    updateStatistics() {
        const steps = this.currentConfig.steps || {};
        
        // Total steps
        document.getElementById('total-steps').textContent = Object.keys(steps).length;
        
        // Parallel capable (steps with no dependencies)
        const parallelSteps = Object.values(steps).filter(step => 
            !step.depends_on || step.depends_on.length === 0
        ).length;
        document.getElementById('parallel-steps').textContent = parallelSteps;
        
        // Review steps
        const reviewSteps = Object.keys(steps).filter(stepName => 
            stepName.includes('review')
        ).length;
        document.getElementById('review-steps').textContent = reviewSteps;
        
        // Estimated duration
        const totalTimeout = Object.values(steps).reduce((sum, step) => 
            sum + (step.timeout || 300), 0
        );
        const estimatedMinutes = Math.ceil(totalTimeout / 60);
        document.getElementById('estimated-time').textContent = `${estimatedMinutes}min`;
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refresh-pipeline-viz')?.addEventListener('click', () => {
            this.refreshVisualization();
        });
        
        // Expand button
        document.getElementById('expand-pipeline-viz')?.addEventListener('click', () => {
            this.expandVisualization();
        });
        
        // Edit button (admin only)
        document.getElementById('edit-pipeline-config')?.addEventListener('click', () => {
            this.openEditor();
        });
        
        // Listen for configuration updates
        window.addEventListener('pipelineConfigUpdated', () => {
            this.refreshVisualization();
        });
    }
    
    async refreshVisualization() {
        await this.loadConfiguration();
        await this.renderVisualization();
    }
    
    expandVisualization() {
        const container = this.container.querySelector('.pipeline-visualization');
        if (container.classList.contains('expanded')) {
            container.classList.remove('expanded');
        } else {
            container.classList.add('expanded');
        }
    }
    
    openEditor() {
        // Navigate to pipeline editor or open in modal
        if (this.isAdmin()) {
            window.location.href = '/pipeline-editor.html';
        }
    }
    
    isAdmin() {
        return localStorage.getItem('userRole') === 'admin';
    }
    
    parseYAML(yamlContent) {
        // In a real implementation, use js-yaml
        try {
            // This is a very simplified parser for demo purposes
            const lines = yamlContent.split('\n');
            const result = { steps: {}, models: {}, branches: {} };
            
            let currentSection = null;
            let currentStep = null;
            
            lines.forEach(line => {
                const trimmed = line.trim();
                if (trimmed.startsWith('steps:')) {
                    currentSection = 'steps';
                } else if (trimmed.startsWith('models:')) {
                    currentSection = 'models';
                } else if (trimmed.startsWith('branches:')) {
                    currentSection = 'branches';
                } else if (trimmed && !trimmed.startsWith('#') && trimmed.includes(':')) {
                    if (currentSection === 'steps' && !trimmed.startsWith(' ')) {
                        currentStep = trimmed.split(':')[0];
                        result.steps[currentStep] = {
                            description: currentStep,
                            depends_on: [],
                            timeout: 300
                        };
                    }
                }
            });
            
            return result;
        } catch (error) {
            console.error('YAML parsing error:', error);
            return this.getDefaultConfig();
        }
    }
    
    getDefaultConfig() {
        return {
            steps: {
                idea_generation: {
                    description: "Generate research ideas",
                    depends_on: [],
                    timeout: 120
                },
                technical_design: {
                    description: "Create technical design",
                    depends_on: ["idea_generation"],
                    timeout: 300
                },
                code_generation: {
                    description: "Generate code",
                    depends_on: ["technical_design"],
                    timeout: 420
                },
                paper_writing: {
                    description: "Write research paper",
                    depends_on: ["code_generation"],
                    timeout: 600
                }
            }
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize on about page or anywhere with pipeline visualization
    if (document.getElementById('pipeline-visualization-container')) {
        window.pipelineVisualization = new PipelineVisualization('pipeline-visualization-container');
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PipelineVisualization;
}