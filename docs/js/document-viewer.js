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
            
            // Load relevant reviews for this document
            documentData.reviews = await this.getRelevantReviews(id, type);
            
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
            
            // Load comments for the issue
            let comments = [];
            try {
                if (window.githubAuth) {
                    comments = await window.githubAuth.getComments(issueNumber);
                }
            } catch (error) {
                console.error('Error loading comments:', error);
                comments = [];
            }
            
            return {
                type: 'issue',
                title: issue.title,
                meta: {
                    'Issue Number': `#${issue.number}`,
                    'Created': new Date(issue.created_at).toLocaleDateString(),
                    'Author': issue.realAuthor ? issue.realAuthor.name : issue.user.login,
                    'Status': issue.projectStatus || 'Backlog',
                    'Comments': comments.length,
                    'Upvotes': issue.votes?.up || 0,
                    'Downvotes': issue.votes?.down || 0
                },
                content: this.formatMarkdown(issue.body || 'No description provided'),
                comments: comments,
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
        // Get design from loaded data
        const design = window.allData?.designs?.find(d => d.id === designId);
        if (!design) {
            throw new Error('Design not found');
        }
        
        let content = 'Design document content would be loaded here.';
        if (design.designUrl && design.designUrl.includes('github.com')) {
            try {
                // Extract path from GitHub URL and load content
                const pathMatch = design.designUrl.match(/github\.com\/[^/]+\/[^/]+\/blob\/[^/]+\/(.+)/);
                if (pathMatch) {
                    content = await window.api.fetchFileContent(pathMatch[1]);
                }
            } catch (error) {
                console.error('Error loading design content:', error);
            }
        }
        
        return {
            type: 'design',
            title: design.title,
            meta: {
                'Project ID': design.id,
                'Date': design.date ? new Date(design.date).toLocaleDateString() : 'Unknown',
                'Author': design.author || 'Unknown',
                'Status': design.status || 'Design'
            },
            content: this.formatMarkdown(content),
            links: [
                { text: 'Related Issue', url: design.issueUrl, icon: 'link' },
                { text: 'View File', url: design.designUrl, icon: 'file-alt' }
            ].filter(link => link.url),
            allowReview: true,
            reviewType: 'Design'
        };
    },
    
    async loadPlan(planId) {
        // Get plan from loaded data
        const plan = window.allData?.plans?.find(p => p.id === planId);
        if (!plan) {
            throw new Error('Plan not found');
        }
        
        let content = 'Implementation plan content would be loaded here.';
        if (plan.planUrl && plan.planUrl.includes('github.com')) {
            try {
                // Extract path from GitHub URL and load content
                const pathMatch = plan.planUrl.match(/github\.com\/[^/]+\/[^/]+\/blob\/[^/]+\/(.+)/);
                if (pathMatch) {
                    content = await window.api.fetchFileContent(pathMatch[1]);
                }
            } catch (error) {
                console.error('Error loading plan content:', error);
            }
        }
        
        return {
            type: 'plan',
            title: plan.title,
            meta: {
                'Project ID': plan.id,
                'Date': plan.date ? new Date(plan.date).toLocaleDateString() : 'Unknown',
                'Author': plan.author || 'Unknown',
                'Status': plan.status || 'Ready'
            },
            content: this.formatMarkdown(content),
            links: [
                { text: 'Related Issue', url: plan.issueUrl, icon: 'link' },
                { text: 'View File', url: plan.planUrl, icon: 'file-alt' }
            ].filter(link => link.url),
            allowReview: true,
            reviewType: 'Implementation'
        };
    },
    
    async loadPaper(paperId) {
        // Get paper from loaded data
        const paper = [...(window.allData?.papersCompleted || []), ...(window.allData?.papersInProgress || [])].find(p => p.id === paperId);
        if (!paper) {
            throw new Error('Paper not found');
        }
        
        let content = 'Paper content would be loaded here.';
        if (paper.paperUrl && paper.paperUrl.includes('github.com')) {
            try {
                // Extract path from GitHub URL and load content
                const pathMatch = paper.paperUrl.match(/github\.com\/[^/]+\/[^/]+\/blob\/[^/]+\/(.+)/);
                if (pathMatch) {
                    content = await window.api.fetchFileContent(pathMatch[1]);
                }
            } catch (error) {
                console.error('Error loading paper content:', error);
            }
        }
        
        return {
            type: 'paper',
            title: paper.title,
            meta: {
                'Project ID': paper.id,
                'Contributors': paper.authors || 'Unknown',
                'Status': paper.status === 'completed' ? 'Completed' : 'In Progress'
            },
            content: this.formatMarkdown(content),
            links: [
                { text: 'Paper', url: paper.paperUrl, icon: 'file-pdf' },
                { text: 'Source Code', url: paper.codeUrl, icon: 'code' },
                { text: 'Dataset', url: paper.dataUrl, icon: 'database' }
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
                
                ${documentData.comments && documentData.comments.length > 0 ? `
                    <div class="document-comments">
                        <h3><i class="fas fa-comments"></i> Comments (${documentData.comments.length})</h3>
                        <div class="comments-list">
                            ${documentData.comments.map(comment => `
                                <div class="comment">
                                    <div class="comment-header">
                                        <img src="${comment.user.avatar_url}" alt="${comment.user.login}" class="comment-avatar">
                                        <div class="comment-meta">
                                            <strong>${comment.user.login}</strong>
                                            <span class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                    <div class="comment-body">
                                        ${this.formatMarkdown(comment.body)}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${documentData.reviews && documentData.reviews.length > 0 ? `
                    <div class="document-reviews">
                        <h3><i class="fas fa-star"></i> Reviews (${documentData.reviews.length})</h3>
                        <div class="reviews-list">
                            ${documentData.reviews.map(review => `
                                <div class="review-item">
                                    <div class="review-header">
                                        <div class="review-meta">
                                            <strong>${this.escapeHtml(review.reviewer)}</strong>
                                            <span class="review-type">${this.escapeHtml(review.type)}</span>
                                            <span class="review-date">${new Date(review.date).toLocaleDateString()}</span>
                                        </div>
                                        ${review.reviewUrl ? `
                                            <a href="${review.reviewUrl}" target="_blank" class="review-link">
                                                <i class="fas fa-external-link-alt"></i> View Full Review
                                            </a>
                                        ` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="document-footer">
                    <div class="document-voting">
                        <button class="vote-btn" onclick="documentViewer.vote(${this.currentDocument?.id}, '+1')" id="vote-up-${this.currentDocument?.id}">
                            <i class="fas fa-thumbs-up"></i> <span id="upvote-count-${this.currentDocument?.id}">${documentData.meta.Upvotes || 0}</span>
                        </button>
                        <button class="vote-btn" onclick="documentViewer.vote(${this.currentDocument?.id}, '-1')" id="vote-down-${this.currentDocument?.id}">
                            <i class="fas fa-thumbs-down"></i> <span id="downvote-count-${this.currentDocument?.id}">${documentData.meta.Downvotes || 0}</span>
                        </button>
                    </div>
                    ${documentData.allowReview ? `
                        <button class="btn-primary" onclick="documentViewer.showReviewForm()">
                            <i class="fas fa-star"></i> Add Review
                        </button>
                    ` : ''}
                </div>
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
    
    async vote(issueNumber, reaction) {
        try {
            await window.api.addReaction(issueNumber, reaction);
            
            // Update the vote counts in the modal
            const issue = allData.backlog.find(item => item.number === issueNumber);
            if (issue) {
                if (reaction === '+1') {
                    issue.votes.up = (issue.votes.up || 0) + 1;
                    const upvoteElement = document.getElementById(`upvote-count-${issueNumber}`);
                    if (upvoteElement) {
                        upvoteElement.textContent = issue.votes.up;
                    }
                } else if (reaction === '-1') {
                    issue.votes.down = (issue.votes.down || 0) + 1;
                    const downvoteElement = document.getElementById(`downvote-count-${issueNumber}`);
                    if (downvoteElement) {
                        downvoteElement.textContent = issue.votes.down;
                    }
                }
            }
            
        } catch (error) {
            console.error('Error voting:', error);
            alert('Error adding vote. Please try again.');
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
        const result = await window.api.createFile(
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
    
    async getRelevantReviews(documentId, documentType) {
        try {
            // Get all reviews from loaded data
            const allReviews = window.allData?.reviews || [];
            
            // Filter reviews for this specific document
            const relevantReviews = allReviews.filter(review => {
                // Match by project ID
                return review.projectId === documentId || review.id === documentId;
            });
            
            console.log(`Found ${relevantReviews.length} reviews for ${documentType} ${documentId}`);
            return relevantReviews;
            
        } catch (error) {
            console.error('Error loading relevant reviews:', error);
            return [];
        }
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