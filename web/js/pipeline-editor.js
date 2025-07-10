/**
 * Pipeline Editor Component
 * Provides web-based YAML editing with validation and visualization
 */

class PipelineEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.editor = null;
        this.currentConfig = null;
        this.validationErrors = [];
        this.isAdmin = false;
        
        this.init();
    }
    
    async init() {
        this.checkAdminStatus();
        await this.setupEditor();
        await this.loadCurrentConfig();
        this.setupEventListeners();
        this.updateVisualization();
    }
    
    checkAdminStatus() {
        // Check if user has admin privileges
        const userRole = localStorage.getItem('userRole');
        this.isAdmin = userRole === 'admin';
        
        if (!this.isAdmin) {
            this.container.innerHTML = `
                <div class="access-denied">
                    <h3>🔒 Admin Access Required</h3>
                    <p>Pipeline editing requires administrator privileges.</p>
                </div>
            `;
            return;
        }
    }
    
    async setupEditor() {
        if (!this.isAdmin) return;
        
        // Create editor container
        this.container.innerHTML = `
            <div class="pipeline-editor-container">
                <div class="editor-header">
                    <h2>🔧 Pipeline Configuration Editor</h2>
                    <div class="editor-controls">
                        <button id="load-config" class="btn btn-secondary">Load</button>
                        <button id="validate-config" class="btn btn-info">Validate</button>
                        <button id="save-config" class="btn btn-success">Save</button>
                        <button id="reset-config" class="btn btn-warning">Reset</button>
                    </div>
                </div>
                
                <div class="editor-main">
                    <div class="editor-panel">
                        <div class="panel-header">
                            <h3>YAML Configuration</h3>
                            <div class="validation-status" id="validation-status">
                                <span class="status-indicator">⏳</span>
                                <span class="status-text">Not validated</span>
                            </div>
                        </div>
                        <div id="yaml-editor" class="yaml-editor"></div>
                    </div>
                    
                    <div class="visualization-panel">
                        <div class="panel-header">
                            <h3>Pipeline Visualization</h3>
                            <div class="viz-controls">
                                <button id="refresh-viz" class="btn btn-sm btn-info">Refresh</button>
                                <button id="export-viz" class="btn btn-sm btn-secondary">Export</button>
                            </div>
                        </div>
                        <div id="pipeline-flowchart" class="flowchart-container"></div>
                    </div>
                </div>
                
                <div class="editor-footer">
                    <div class="validation-results" id="validation-results"></div>
                </div>
            </div>
        `;
        
        // Initialize Monaco Editor
        await this.initMonacoEditor();
    }
    
    async initMonacoEditor() {
        // Load Monaco Editor (assuming it's available)
        if (typeof monaco === 'undefined') {
            console.error('Monaco Editor not available');
            return;
        }
        
        // Configure YAML language support
        monaco.languages.setLanguageConfiguration('yaml', {
            brackets: [['[', ']'], ['(', ')']],
            autoClosingPairs: [
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '"', close: '"' },
                { open: "'", close: "'" }
            ]
        });
        
        // Create editor instance
        this.editor = monaco.editor.create(document.getElementById('yaml-editor'), {
            value: '# Loading configuration...',
            language: 'yaml',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            lineNumbers: 'on',
            folding: true,
            selectOnLineNumbers: true
        });
        
        // Setup real-time validation
        this.editor.onDidChangeModelContent(() => {
            this.validateConfigurationDebounced();
        });
    }
    
    async loadCurrentConfig() {
        try {
            const response = await fetch('/api/pipeline/config');
            if (response.ok) {
                const config = await response.text();
                this.currentConfig = config;
                
                if (this.editor) {
                    this.editor.setValue(config);
                }
                
                this.updateValidationStatus('loaded', 'Configuration loaded');
            } else {
                throw new Error(`Failed to load config: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.updateValidationStatus('error', `Failed to load: ${error.message}`);
        }
    }
    
    async saveConfiguration() {
        if (!this.editor) return;
        
        const yamlContent = this.editor.getValue();
        
        // Validate before saving
        const isValid = await this.validateConfiguration(yamlContent, true);
        if (!isValid) {
            alert('Configuration has validation errors. Please fix them before saving.');
            return;
        }
        
        try {
            const response = await fetch('/api/pipeline/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-yaml',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: yamlContent
            });
            
            if (response.ok) {
                this.currentConfig = yamlContent;
                this.updateValidationStatus('saved', 'Configuration saved successfully');
                this.updateVisualization();
                
                // Trigger visualization update on about page
                this.notifyVisualizationUpdate();
            } else {
                throw new Error(`Save failed: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.updateValidationStatus('error', `Save failed: ${error.message}`);
        }
    }
    
    async validateConfiguration(yamlContent = null, showResults = false) {
        const content = yamlContent || (this.editor ? this.editor.getValue() : '');
        
        try {
            const response = await fetch('/api/pipeline/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-yaml'
                },
                body: content
            });
            
            const result = await response.json();
            
            if (result.valid) {
                this.validationErrors = [];
                this.updateValidationStatus('valid', 'Configuration is valid');
                this.clearValidationResults();
                return true;
            } else {
                this.validationErrors = result.errors || [];
                this.updateValidationStatus('invalid', `${this.validationErrors.length} validation errors`);
                
                if (showResults) {
                    this.showValidationResults(this.validationErrors);
                }
                
                return false;
            }
        } catch (error) {
            console.error('Validation error:', error);
            this.updateValidationStatus('error', `Validation failed: ${error.message}`);
            return false;
        }
    }
    
    validateConfigurationDebounced = this.debounce(this.validateConfiguration.bind(this), 1000);
    
    updateValidationStatus(status, message) {
        const statusElement = document.getElementById('validation-status');
        if (!statusElement) return;
        
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('.status-text');
        
        const statusConfig = {
            loaded: { icon: '📋', class: 'status-loaded' },
            valid: { icon: '✅', class: 'status-valid' },
            invalid: { icon: '❌', class: 'status-invalid' },
            saved: { icon: '💾', class: 'status-saved' },
            error: { icon: '🔥', class: 'status-error' }
        };
        
        const config = statusConfig[status] || { icon: '⏳', class: 'status-unknown' };
        
        indicator.textContent = config.icon;
        text.textContent = message;
        
        // Update CSS classes
        statusElement.className = `validation-status ${config.class}`;
    }
    
    showValidationResults(errors) {
        const resultsContainer = document.getElementById('validation-results');
        if (!resultsContainer) return;
        
        if (errors.length === 0) {
            resultsContainer.innerHTML = '';
            return;
        }
        
        const errorList = errors.map(error => `
            <div class="validation-error">
                <span class="error-icon">❌</span>
                <span class="error-message">${this.escapeHtml(error)}</span>
            </div>
        `).join('');
        
        resultsContainer.innerHTML = `
            <div class="validation-errors">
                <h4>Validation Errors (${errors.length})</h4>
                ${errorList}
            </div>
        `;
    }
    
    clearValidationResults() {
        const resultsContainer = document.getElementById('validation-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    }
    
    async updateVisualization() {
        const flowchartContainer = document.getElementById('pipeline-flowchart');
        if (!flowchartContainer) return;
        
        try {
            // Generate Mermaid flowchart from current config
            const yamlContent = this.editor ? this.editor.getValue() : this.currentConfig;
            const mermaidCode = await this.generateMermaidDiagram(yamlContent);
            
            // Render with Mermaid
            if (typeof mermaid !== 'undefined') {
                flowchartContainer.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
                mermaid.init(undefined, flowchartContainer.querySelector('.mermaid'));
            } else {
                flowchartContainer.innerHTML = `
                    <div class="visualization-placeholder">
                        <p>Mermaid.js not available for visualization</p>
                        <pre>${mermaidCode}</pre>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Visualization error:', error);
            flowchartContainer.innerHTML = `
                <div class="visualization-error">
                    <p>Failed to generate visualization: ${error.message}</p>
                </div>
            `;
        }
    }
    
    async generateMermaidDiagram(yamlContent) {
        try {
            const response = await fetch('/api/pipeline/mermaid', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-yaml'
                },
                body: yamlContent
            });
            
            if (response.ok) {
                const result = await response.json();
                return result.mermaid;
            } else {
                throw new Error('Failed to generate Mermaid diagram');
            }
        } catch (error) {
            // Fallback: generate simple diagram client-side
            return this.generateSimpleMermaidDiagram(yamlContent);
        }
    }
    
    generateSimpleMermaidDiagram(yamlContent) {
        // Simple client-side Mermaid generation
        try {
            const config = this.parseYAML(yamlContent);
            const steps = config.steps || {};
            
            let mermaid = 'graph TD\n';
            
            // Add nodes
            Object.keys(steps).forEach(stepName => {
                const step = steps[stepName];
                const label = step.description || stepName;
                mermaid += `    ${stepName}["${label}"]\n`;
            });
            
            // Add edges
            Object.entries(steps).forEach(([stepName, step]) => {
                const dependencies = step.depends_on || [];
                dependencies.forEach(dep => {
                    if (steps[dep]) {
                        mermaid += `    ${dep} --> ${stepName}\n`;
                    }
                });
            });
            
            return mermaid;
        } catch (error) {
            return `graph TD\n    Error["Failed to parse configuration"]`;
        }
    }
    
    notifyVisualizationUpdate() {
        // Notify other components that the pipeline has been updated
        window.dispatchEvent(new CustomEvent('pipelineConfigUpdated', {
            detail: { source: 'editor' }
        }));
    }
    
    setupEventListeners() {
        if (!this.isAdmin) return;
        
        // Control buttons
        document.getElementById('load-config')?.addEventListener('click', () => {
            this.loadCurrentConfig();
        });
        
        document.getElementById('validate-config')?.addEventListener('click', () => {
            this.validateConfiguration(null, true);
        });
        
        document.getElementById('save-config')?.addEventListener('click', () => {
            this.saveConfiguration();
        });
        
        document.getElementById('reset-config')?.addEventListener('click', () => {
            if (confirm('Are you sure you want to reset to the last saved configuration?')) {
                if (this.editor && this.currentConfig) {
                    this.editor.setValue(this.currentConfig);
                }
            }
        });
        
        document.getElementById('refresh-viz')?.addEventListener('click', () => {
            this.updateVisualization();
        });
        
        document.getElementById('export-viz')?.addEventListener('click', () => {
            this.exportVisualization();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveConfiguration();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.loadCurrentConfig();
                        break;
                }
            }
        });
    }
    
    exportVisualization() {
        const flowchartElement = document.querySelector('#pipeline-flowchart .mermaid svg');
        if (flowchartElement) {
            const svgData = new XMLSerializer().serializeToString(flowchartElement);
            const blob = new Blob([svgData], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = 'pipeline-diagram.svg';
            a.click();
            
            URL.revokeObjectURL(url);
        }
    }
    
    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    parseYAML(yamlContent) {
        // Simple YAML parser - in production, use a proper library
        try {
            // This is a very basic implementation
            // In a real app, use js-yaml or similar
            return JSON.parse(yamlContent.replace(/:\s*/g, ':').replace(/\n\s*-\s*/g, '\n- '));
        } catch (error) {
            throw new Error('Failed to parse YAML');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on a page with the pipeline editor
    if (document.getElementById('pipeline-editor-container')) {
        window.pipelineEditor = new PipelineEditor('pipeline-editor-container');
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PipelineEditor;
}