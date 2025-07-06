// Document viewer for llmXive site

const DocumentViewer = {
    currentDocument: null,
    
    init() {
        this.setupEventListeners();
    },
    
    setupEventListeners() {
        // Modal close events
        const modal = document.getElementById('documentModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }
        
        // Close button
        const closeBtn = modal?.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }
        
        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen()) {
                this.closeModal();
            }
        });
    },
    
    async openDocument(type, id, data = null) {
        console.log(`Opening ${type} document:`, id);
        
        this.currentDocument = { type, id, data };
        
        try {
            let documentData;
            
            switch (type) {
                case 'issue':
                    documentData = await this.loadIssue(id);
                    break;
                case 'design':
                    documentData = await this.loadDesign(id);
                    break;
                case 'plan':
                    documentData = await this.loadPlan(id);
                    break;
                case 'paper':
                    documentData = await this.loadPaper(id);
                    break;
                default:
                    throw new Error(`Unknown document type: ${type}`);
            }
            
            this.renderDocument(documentData);
            this.showModal();
            
        } catch (error) {
            console.error('Error loading document:', error);
            this.showError(error.message);
        }
    },
    
    async loadIssue(issueNumber) {
        try {
            // Get the issue from the currently loaded backlog data
            const issue = allData.backlog.find(item => item.number === issueNumber);
            
            if (!issue) {
                throw new Error('Issue not found');
            }
            
            return {
                type: 'issue',
                title: issue.title,
                meta: {
                    'Issue Number': `#${issue.number}`,
                    'Created': new Date(issue.created_at).toLocaleDateString(),
                    'Author': issue.realAuthor ? issue.realAuthor.name : issue.user.login,
                    'Status': issue.projectStatus || 'Backlog',
                    'Comments': issue.comments || 0,
                    'Upvotes': issue.votes?.up || 0
                },
                content: this.formatMarkdown(issue.body || 'No description provided'),
                links: [
                    { text: 'View on GitHub', url: issue.html_url, icon: 'external-link-alt' }
                ],
                allowReview: true, // Allow reviews for ideas
                reviewType: 'Idea'
            };
        } catch (error) {
            console.error('Error loading issue:', error);
            throw new Error(`Failed to load issue: ${error.message}`);
        }
    },
    
    async loadDesign(designId) {
        const design = await githubAPI.getTechnicalDesign(designId);
        const content = await githubAPI.getFileContent(design.designPath);
        
        return {
            type: 'design',
            title: design.title,
            meta: {
                'Project ID': design.id,
                'Date': new Date(design.date).toLocaleDateString(),
                'Author': design.author,
                'Status': design.status
            },
            content: this.formatMarkdown(content),
            links: [
                { text: 'Related Issue', url: design.issueUrl, icon: 'link' },
                { text: 'View File', url: design.designUrl, icon: 'file-alt' }
            ],
            allowReview: true,
            reviewType: 'Design'
        };
    },
    
    async loadPlan(planId) {
        const plan = await githubAPI.getImplementationPlan(planId);
        const content = await githubAPI.getFileContent(plan.planPath);
        
        return {
            type: 'plan',
            title: plan.title,
            meta: {
                'Project ID': plan.id,
                'Date': new Date(plan.date).toLocaleDateString(),
                'Author': plan.author,
                'Status': plan.status
            },
            content: this.formatMarkdown(content),
            links: [
                { text: 'Related Issue', url: plan.issueUrl, icon: 'link' },
                { text: 'View File', url: plan.planUrl, icon: 'file-alt' },
                { text: 'Technical Design', url: plan.designUrl, icon: 'drafting-compass' }
            ],
            allowReview: true,
            reviewType: 'Implementation'
        };
    },
    
    async loadPaper(paperId) {
        const paper = await githubAPI.getPaper(paperId);
        const content = await githubAPI.getFileContent(paper.paperPath);
        
        return {
            type: 'paper',
            title: paper.title,
            meta: {
                'Project ID': paper.id,
                'Date': new Date(paper.date).toLocaleDateString(),
                'Contributors': paper.contributors.join(', '),
                'Status': paper.status
            },
            content: this.formatMarkdown(content),
            links: [
                { text: 'Paper PDF', url: paper.pdfUrl, icon: 'file-pdf' },
                { text: 'Source Code', url: paper.codeUrl, icon: 'code' },
                { text: 'Dataset', url: paper.dataUrl, icon: 'database' },
                { text: 'Technical Design', url: paper.designUrl, icon: 'drafting-compass' },
                { text: 'Implementation Plan', url: paper.planUrl, icon: 'project-diagram' }
            ].filter(link => link.url), // Only include links that exist
            allowReview: true,
            reviewType: 'Paper'
        };
    },
    
    renderDocument(documentData) {
        const modalContent = document.getElementById('documentModalContent');
        if (!modalContent) return;
        
        const html = `
            <div class="document-content">
                <div class="document-header">
                    <h2 class="document-title">${this.escapeHtml(documentData.title)}</h2>
                    <div class="document-meta">
                        ${Object.entries(documentData.meta).map(([key, value]) => 
                            `<span><strong>${key}:</strong> ${this.escapeHtml(value)}</span>`
                        ).join('')}
                    </div>
                    ${documentData.links.length > 0 ? `
                        <div class="document-links">
                            ${documentData.links.map(link => 
                                `<a href="${link.url}" target="_blank" class="card-link">
                                    <i class="fas fa-${link.icon}"></i> ${link.text}
                                </a>`
                            ).join('')}
                        </div>
                    ` : ''}
                </div>
                <div class="document-body">
                    ${documentData.content}
                </div>
                
                ${documentData.allowReview ? `
                    <div class="document-actions">
                        <button class="btn-primary" onclick="documentViewer.showReviewForm()">
                            <i class="fas fa-star"></i> Add Review
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
        
        modalContent.innerHTML = html;
        
        // Initially hide the human review section
        const reviewSection = document.getElementById('humanReviewSection');
        if (reviewSection) {
            reviewSection.style.display = 'none';
            if (documentData.allowReview) {
                this.setupReviewForm(documentData);
            }
        }
    },
    
    showReviewForm() {
        const reviewSection = document.getElementById('humanReviewSection');
        if (reviewSection) {
            reviewSection.style.display = 'block';
            reviewSection.scrollIntoView({ behavior: 'smooth' });
        }
    },
    
    setupReviewForm(documentData) {
        const form = document.getElementById('humanReviewForm');
        if (!form) return;
        
        // Store document data for review submission
        form.dataset.documentType = documentData.type;
        form.dataset.documentId = this.currentDocument.id;
        form.dataset.reviewType = documentData.reviewType;
        
        // Reset form
        form.reset();
        
        // Set up form submission
        form.onsubmit = (e) => this.handleReviewSubmission(e);
    },
    
    async handleReviewSubmission(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        
        const reviewData = {
            documentType: form.dataset.documentType,
            documentId: form.dataset.documentId,
            reviewType: form.dataset.reviewType,
            summary: formData.get('reviewSummary') || document.getElementById('reviewSummary').value,
            strengths: formData.get('reviewStrengths') || document.getElementById('reviewStrengths').value,
            concerns: formData.get('reviewConcerns') || document.getElementById('reviewConcerns').value,
            minorConcerns: formData.get('reviewMinorConcerns') || document.getElementById('reviewMinorConcerns').value,
            score: formData.get('reviewScore') || document.getElementById('reviewScore').value
        };
        
        try {
            console.log('Submitting human review:', reviewData);
            
            // Submit review via GitHub API
            const result = await this.submitHumanReview(reviewData);
            
            if (result) {
                alert('Review submitted successfully!');
                this.closeModal();
            }
            
        } catch (error) {
            console.error('Error submitting review:', error);
            alert('Error submitting review. Please try again.');
        }
    },
    
    async submitHumanReview(reviewData) {
        // Generate review content
        const reviewContent = this.formatReviewContent(reviewData);
        
        // Generate unique review ID
        const reviewId = `human__${new Date().toISOString().split('T')[0].replace(/-/g, '-')}__M.md`;
        
        // Determine file path
        const reviewPath = `reviews/${reviewData.documentId}/${reviewData.reviewType}/${reviewId}`;
        
        // Create the review file
        const result = await githubAPI.createFile(
            reviewPath,
            reviewContent,
            `Add human review for ${reviewData.documentType} ${reviewData.documentId}`
        );
        
        if (result) {
            // Also update the reviews README table
            await this.updateReviewsTable(reviewData, reviewPath);
        }
        
        return result;
    },
    
    formatReviewContent(reviewData) {
        const date = new Date().toISOString().split('T')[0];
        const score = parseFloat(reviewData.score);
        const recommendation = this.getRecommendationText(score);
        
        return `# ${reviewData.reviewType} Review

**Reviewer**: Human
**Date**: ${date}
**Score**: ${score}

## Overall Summary
${reviewData.summary}

## Major Strengths
${reviewData.strengths || 'None specified'}

## Major Concerns  
${reviewData.concerns || 'None specified'}

## Minor Concerns
${reviewData.minorConcerns || 'None specified'}

## Recommendation
${recommendation}

---
*This review was submitted through the llmXive web interface.*`;
    },
    
    getRecommendationText(score) {
        if (score >= 1.0) return 'Strong Accept';
        if (score >= 0.7) return 'Accept';
        if (score >= 0.3) return 'Weak Accept';
        return 'Reject';
    },
    
    async updateReviewsTable(reviewData, reviewPath) {
        // This would update the reviews README table
        // Implementation would depend on GitHub API capabilities
        console.log('Would update reviews table with:', reviewData, reviewPath);
    },
    
    getIssueStatus(labels) {
        const labelNames = labels.map(l => l.name);
        if (labelNames.includes('in-progress')) return 'In Progress';
        if (labelNames.includes('ready')) return 'Ready';
        if (labelNames.includes('done')) return 'Done';
        if (labelNames.includes('backlog')) return 'Backlog';
        return 'Unknown';
    },
    
    formatMarkdown(content) {
        // Basic markdown formatting
        // In a real implementation, you'd use a proper markdown parser
        return content
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.+)$/gm, '<p>$1</p>')
            .replace(/^<p><h/g, '<h')
            .replace(/<\/h([1-6])><\/p>$/g, '</h$1>');
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    showModal() {
        const modal = document.getElementById('documentModal');
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    },
    
    closeModal() {
        const modal = document.getElementById('documentModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        
        this.currentDocument = null;
    },
    
    isModalOpen() {
        const modal = document.getElementById('documentModal');
        return modal && modal.style.display === 'flex';
    },
    
    showError(message) {
        const modalContent = document.getElementById('documentModalContent');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Document</h3>
                    <p>${this.escapeHtml(message)}</p>
                </div>
            `;
        }
        this.showModal();
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    DocumentViewer.init();
});

// Global functions for opening modals (called from card clicks)
function openIssueModal(issueNumber) {
    DocumentViewer.openDocument('issue', issueNumber);
}

function openDesignModal(designId) {
    DocumentViewer.openDocument('design', designId);
}

function openPlanModal(planId) {
    DocumentViewer.openDocument('plan', planId);
}

function openPaperModal(paperId) {
    DocumentViewer.openDocument('paper', paperId);
}

function closeDocumentModal() {
    DocumentViewer.closeModal();
}

function cancelReview() {
    const form = document.getElementById('humanReviewForm');
    if (form) {
        form.reset();
    }
}

// Export for other modules
window.documentViewer = DocumentViewer;