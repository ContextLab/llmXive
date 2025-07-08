/**
 * Document Viewer Component for llmXive
 * 
 * Handles viewing project documents within the website with GitHub links
 */

class DocumentViewer {
    constructor() {
        this.createModal();
    }

    createModal() {
        // Create document viewer modal if it doesn't exist
        if (document.getElementById('document-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'document-modal';
        modal.className = 'document-modal';
        modal.innerHTML = `
            <div class="document-modal-content">
                <div class="document-modal-header">
                    <div class="document-info">
                        <h2 class="document-title" id="document-title">Document Title</h2>
                        <div class="document-meta">
                            <span class="document-type" id="document-type">Type</span>
                            <a href="#" class="github-link" id="github-link" target="_blank">View on GitHub</a>
                        </div>
                    </div>
                    <button class="document-close" onclick="documentViewer.closeDocument()">&times;</button>
                </div>
                <div class="document-modal-body">
                    <div class="document-content" id="document-content">
                        <!-- Document content will be loaded here -->
                    </div>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .document-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 2000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                backdrop-filter: blur(8px);
            }

            .document-modal.show {
                opacity: 1;
                visibility: visible;
            }

            .document-modal-content {
                background: var(--surface-elevated, #ffffff);
                border-radius: var(--radius-xl, 24px);
                max-width: 90vw;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transform: scale(0.9) translateY(20px);
                transition: all 0.3s ease;
                box-shadow: var(--shadow-xl, 0 20px 25px -5px rgb(0 0 0 / 0.1));
                border: 1px solid var(--border, #e5e7eb);
            }

            .document-modal.show .document-modal-content {
                transform: scale(1) translateY(0);
            }

            .document-modal-header {
                padding: 2rem 2rem 1rem;
                border-bottom: 1px solid var(--border, #e5e7eb);
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                background: var(--surface, #f9fafb);
            }

            .document-info {
                flex: 1;
                margin-right: 1rem;
            }

            .document-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-primary, #111827);
                margin-bottom: 0.5rem;
                line-height: 1.3;
            }

            .document-meta {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .document-type {
                display: inline-block;
                background: var(--primary-bg, #eef2ff);
                color: var(--primary-dark, #4f46e5);
                font-size: 0.75rem;
                font-weight: 500;
                padding: 0.25rem 0.75rem;
                border-radius: var(--radius-sm, 8px);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .github-link {
                color: var(--primary, #6366f1);
                text-decoration: none;
                font-size: 0.875rem;
                font-weight: 500;
                transition: var(--transition, all 0.2s ease);
            }

            .github-link:hover {
                text-decoration: underline;
            }

            .document-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                color: var(--text-tertiary, #9ca3af);
                cursor: pointer;
                padding: 0.5rem;
                border-radius: var(--radius-md, 12px);
                transition: var(--transition, all 0.2s ease);
            }

            .document-close:hover {
                background: var(--gray-100, #f3f4f6);
                color: var(--text-primary, #111827);
            }

            .document-modal-body {
                flex: 1;
                overflow-y: auto;
                padding: 2rem;
                background: var(--background, #ffffff);
            }

            .document-content {
                max-width: none;
                line-height: 1.7;
                color: var(--text-primary, #111827);
            }

            .document-content h1,
            .document-content h2,
            .document-content h3,
            .document-content h4,
            .document-content h5,
            .document-content h6 {
                color: var(--text-primary, #111827);
                margin-top: 2rem;
                margin-bottom: 1rem;
                font-weight: 600;
            }

            .document-content h1 { font-size: 2rem; }
            .document-content h2 { font-size: 1.5rem; }
            .document-content h3 { font-size: 1.25rem; }

            .document-content p {
                margin-bottom: 1rem;
                color: var(--text-secondary, #4b5563);
            }

            .document-content ul,
            .document-content ol {
                margin-bottom: 1rem;
                padding-left: 1.5rem;
            }

            .document-content li {
                margin-bottom: 0.5rem;
                color: var(--text-secondary, #4b5563);
            }

            .document-content code {
                background: var(--gray-100, #f3f4f6);
                padding: 0.25rem 0.5rem;
                border-radius: var(--radius-sm, 8px);
                font-family: var(--font-mono, 'JetBrains Mono', monospace);
                font-size: 0.875rem;
            }

            .document-content pre {
                background: var(--gray-100, #f3f4f6);
                padding: 1rem;
                border-radius: var(--radius-md, 12px);
                overflow-x: auto;
                margin-bottom: 1rem;
            }

            .document-content blockquote {
                border-left: 4px solid var(--primary, #6366f1);
                padding-left: 1rem;
                margin: 1rem 0;
                font-style: italic;
                color: var(--text-secondary, #4b5563);
            }

            .document-content table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1rem;
            }

            .document-content th,
            .document-content td {
                border: 1px solid var(--border, #e5e7eb);
                padding: 0.75rem;
                text-align: left;
            }

            .document-content th {
                background: var(--surface, #f9fafb);
                font-weight: 600;
            }

            .document-loading {
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 200px;
                flex-direction: column;
                gap: 1rem;
                color: var(--text-secondary, #4b5563);
            }

            .document-loading-spinner {
                width: 32px;
                height: 32px;
                border: 2px solid var(--border, #e5e7eb);
                border-top: 2px solid var(--primary, #6366f1);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            .document-error {
                text-align: center;
                padding: 2rem;
                color: var(--error, #ef4444);
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            @media (max-width: 768px) {
                .document-modal-content {
                    max-width: 95vw;
                    max-height: 95vh;
                }

                .document-modal-header {
                    padding: 1.5rem 1.5rem 1rem;
                }

                .document-modal-body {
                    padding: 1.5rem;
                }

                .document-meta {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 0.5rem;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(modal);

        // Close modal on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeDocument();
            }
        });

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                this.closeDocument();
            }
        });
    }

    async openDocument(filePath, documentType, projectId) {
        const modal = document.getElementById('document-modal');
        const title = document.getElementById('document-title');
        const type = document.getElementById('document-type');
        const githubLink = document.getElementById('github-link');
        const content = document.getElementById('document-content');

        // Set document info
        title.textContent = this.getDocumentTitle(filePath, documentType);
        type.textContent = documentType;
        githubLink.href = `https://github.com/ContextLab/llmXive/blob/main/${filePath}`;

        // Show modal
        modal.classList.add('show');

        // Load content
        content.innerHTML = `
            <div class="document-loading">
                <div class="document-loading-spinner"></div>
                <p>Loading document...</p>
            </div>
        `;

        try {
            await this.loadDocumentContent(filePath, content);
        } catch (error) {
            content.innerHTML = `
                <div class="document-error">
                    <h3>Document not available</h3>
                    <p>This document hasn't been created yet or is not accessible.</p>
                    <p><a href="${githubLink.href}" target="_blank">View on GitHub</a> to check if it exists in the repository.</p>
                </div>
            `;
        }
    }

    async loadDocumentContent(filePath, contentElement) {
        const GITHUB_BASE = 'https://raw.githubusercontent.com/ContextLab/llmXive/main';
        
        try {
            let content = null;
            let source = 'local';
            
            // Try local file first
            try {
                // Check if we have the completed version first
                const completedPath = filePath.replace('/design.md', '/design-completed.md');
                let response = await fetch(completedPath);
                
                if (!response.ok) {
                    // Fall back to original path
                    response = await fetch(filePath);
                }
                
                if (response.ok) {
                    content = await response.text();
                    source = 'local';
                }
            } catch (localError) {
                console.log('Local file not found, trying GitHub...');
            }
            
            // If local file not found, try GitHub
            if (!content) {
                try {
                    const githubUrl = `${GITHUB_BASE}/${filePath}`;
                    console.log('Fetching from GitHub:', githubUrl);
                    
                    const response = await fetch(githubUrl);
                    if (response.ok) {
                        content = await response.text();
                        source = 'github';
                    }
                } catch (githubError) {
                    console.log('GitHub fetch failed:', githubError);
                }
            }
            
            if (!content) {
                throw new Error('Document not found locally or on GitHub');
            }
            
            // Add source indicator
            const sourceIndicator = source === 'github' ? 
                '<div style="background: var(--primary-bg); color: var(--primary-dark); padding: 0.5rem; border-radius: var(--radius-sm); margin-bottom: 1rem; font-size: 0.875rem;">📡 Loaded from GitHub repository</div>' : '';
            
            if (filePath.endsWith('.md')) {
                contentElement.innerHTML = sourceIndicator + this.renderMarkdown(content);
            } else if (filePath.endsWith('.pdf')) {
                contentElement.innerHTML = `
                    <div style="text-align: center; padding: 2rem;">
                        <h3>PDF Document</h3>
                        <p>PDF viewing is not yet implemented. Please use the GitHub link to view this document.</p>
                        <a href="https://github.com/ContextLab/llmXive/blob/main/${filePath}" 
                           target="_blank" 
                           style="color: var(--primary); text-decoration: none; font-weight: 500;">
                            View PDF on GitHub
                        </a>
                    </div>
                `;
            } else {
                contentElement.innerHTML = sourceIndicator + `<pre><code>${this.escapeHtml(content)}</code></pre>`;
            }
        } catch (error) {
            throw error;
        }
    }

    renderMarkdown(content) {
        // Simple markdown to HTML conversion
        // Remove YAML frontmatter if present
        content = content.replace(/^---[\s\S]*?---\n/, '');
        
        return content
            // Headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Code blocks
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // Inline code
            .replace(/`(.*?)`/g, '<code>$1</code>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Lists
            .replace(/^\- (.*$)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // Paragraphs
            .split('\n\n')
            .map(paragraph => {
                if (paragraph.trim() && 
                    !paragraph.includes('<h') && 
                    !paragraph.includes('<ul>') && 
                    !paragraph.includes('<pre>') &&
                    !paragraph.includes('<li>')) {
                    return `<p>${paragraph.trim()}</p>`;
                }
                return paragraph;
            })
            .join('\n\n');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getDocumentTitle(filePath, documentType) {
        const typeMap = {
            'design': 'Technical Design Document',
            'implementation': 'Implementation Plan',
            'paper': 'Research Paper',
            'code': 'Code Repository',
            'review': 'Review Document'
        };
        return typeMap[documentType] || 'Project Document';
    }

    closeDocument() {
        const modal = document.getElementById('document-modal');
        modal.classList.remove('show');
    }

    // Static method to get available documents for a project
    static getAvailableDocuments(projectId) {
        // Get project data from the global data manager
        const dataManager = window.ProjectDataManager;
        if (!dataManager || !dataManager.loaded) {
            return [];
        }
        
        const project = dataManager.getProject(projectId);
        if (!project) {
            return [];
        }
        
        const possibleDocs = [];
        
        // Primary document from project location
        if (project.location) {
            let documentType = 'design'; // Default to design
            let title = 'Technical Design';
            
            // Determine document type from path
            if (project.location.includes('implementation_plans')) {
                documentType = 'implementation';
                title = 'Implementation Plan';
            } else if (project.location.includes('papers')) {
                documentType = 'paper';
                title = 'Research Paper';
            } else if (project.location.includes('code')) {
                documentType = 'code';
                title = 'Code Repository';
            }
            
            possibleDocs.push({
                title: title,
                type: documentType,
                file: project.location
            });
        }
        
        // Additional documents based on project phase and status
        const expectedDocs = [
            { 
                title: 'Implementation Plan', 
                type: 'implementation', 
                file: `implementation_plans/${projectId}/plan.md`,
                requiredPhase: 'implementation_plan'
            },
            { 
                title: 'Research Paper', 
                type: 'paper', 
                file: `papers/${projectId}/paper.pdf`,
                requiredPhase: 'done'
            },
            { 
                title: 'Code Repository', 
                type: 'code', 
                file: `code/${projectId}/`,
                requiredPhase: 'in_progress'
            }
        ];
        
        // Add documents that are expected based on project phase
        expectedDocs.forEach(doc => {
            // Don't duplicate the primary document
            if (!possibleDocs.some(existing => existing.type === doc.type)) {
                // Only show advanced documents if project has reached appropriate phase
                const phases = ['idea', 'design', 'implementation_plan', 'in_progress', 'review', 'done'];
                const currentPhaseIndex = phases.indexOf(project.phase || project.status);
                const requiredPhaseIndex = phases.indexOf(doc.requiredPhase);
                
                if (currentPhaseIndex >= requiredPhaseIndex) {
                    possibleDocs.push(doc);
                }
            }
        });
        
        return possibleDocs;
    }
}

// Create global instance
window.documentViewer = window.documentViewer || new DocumentViewer();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DocumentViewer;
}

console.log('📄 DocumentViewer loaded');