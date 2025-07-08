/**
 * Review System Component for llmXive
 * 
 * Handles reviewing of ideas, technical designs, implementations, code, data, and papers
 */

class ReviewSystem {
    constructor() {
        this.createReviewModal();
        this.reviews = this.loadReviews();
        this.votes = this.loadVotes();
    }

    createReviewModal() {
        if (document.getElementById('review-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'review-modal';
        modal.className = 'review-modal';
        modal.innerHTML = `
            <div class="review-modal-content">
                <div class="review-modal-header">
                    <h2 class="review-title" id="review-title">Write Review</h2>
                    <button class="modal-close" onclick="reviewSystem.closeReview()">&times;</button>
                </div>
                <div class="review-modal-body">
                    <div class="review-info">
                        <div class="review-project-info" id="review-project-info"></div>
                        <div class="review-type-selector">
                            <label class="review-label">Review Type:</label>
                            <select id="review-type" onchange="reviewSystem.updateReviewForm()">
                                <option value="idea">Project Idea</option>
                                <option value="design">Technical Design</option>
                                <option value="implementation">Implementation Plan</option>
                                <option value="code">Code Review</option>
                                <option value="data">Data Review</option>
                                <option value="paper">Paper Review</option>
                            </select>
                        </div>
                    </div>
                    
                    <form id="review-form" onsubmit="reviewSystem.submitReview(event)">
                        <div class="review-section">
                            <label class="review-label">Overall Assessment</label>
                            <div class="rating-stars" id="overall-rating">
                                ${[1,2,3,4,5].map(i => `
                                    <span class="star" data-rating="${i}" onclick="reviewSystem.setRating('overall', ${i})">★</span>
                                `).join('')}
                            </div>
                            <span class="rating-text" id="overall-rating-text">No rating</span>
                        </div>

                        <div class="review-criteria" id="review-criteria">
                            <!-- Dynamic criteria based on review type -->
                        </div>

                        <div class="review-section">
                            <label class="review-label">Written Review</label>
                            <textarea id="review-text" placeholder="Provide detailed feedback..." rows="6"></textarea>
                        </div>

                        <div class="review-section">
                            <label class="review-label">Recommendation</label>
                            <div class="recommendation-buttons">
                                <button type="button" class="rec-btn" data-rec="accept" onclick="reviewSystem.setRecommendation('accept')">
                                    ✅ Accept
                                </button>
                                <button type="button" class="rec-btn" data-rec="revision" onclick="reviewSystem.setRecommendation('revision')">
                                    🔄 Needs Revision
                                </button>
                                <button type="button" class="rec-btn" data-rec="reject" onclick="reviewSystem.setRecommendation('reject')">
                                    ❌ Reject
                                </button>
                            </div>
                            <input type="hidden" id="recommendation" required>
                        </div>

                        <div class="review-actions">
                            <button type="button" class="review-btn secondary" onclick="reviewSystem.closeReview()">Cancel</button>
                            <button type="submit" class="review-btn primary">Submit Review</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .review-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 3000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .review-modal.show {
                opacity: 1;
                visibility: visible;
            }

            .review-modal-content {
                background: var(--surface-elevated, #ffffff);
                border-radius: var(--radius-xl, 24px);
                max-width: 700px;
                max-height: 90vh;
                overflow-y: auto;
                margin: 2rem;
                transform: scale(0.9) translateY(20px);
                transition: all 0.3s ease;
                box-shadow: var(--shadow-xl, 0 20px 25px -5px rgb(0 0 0 / 0.1));
                border: 1px solid var(--border, #e5e7eb);
            }

            .review-modal.show .review-modal-content {
                transform: scale(1) translateY(0);
            }

            .review-modal-header {
                padding: 2rem 2rem 1rem;
                border-bottom: 1px solid var(--border, #e5e7eb);
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, var(--primary-bg, #eef2ff) 0%, var(--surface, #f9fafb) 100%);
            }

            .review-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-primary, #111827);
                margin: 0;
            }

            .review-modal-body {
                padding: 2rem;
            }

            .review-info {
                background: var(--surface, #f9fafb);
                padding: 1.5rem;
                border-radius: var(--radius-lg, 16px);
                margin-bottom: 2rem;
                border: 1px solid var(--border, #e5e7eb);
            }

            .review-project-info {
                margin-bottom: 1rem;
            }

            .review-type-selector {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .review-label {
                font-weight: 600;
                color: var(--text-primary, #111827);
                margin-bottom: 0.5rem;
                display: block;
            }

            .review-type-selector .review-label {
                margin-bottom: 0;
                min-width: 100px;
            }

            #review-type {
                flex: 1;
                padding: 0.5rem;
                border: 1px solid var(--border, #e5e7eb);
                border-radius: var(--radius-md, 12px);
                font-family: inherit;
            }

            .review-section {
                margin-bottom: 2rem;
            }

            .rating-stars {
                display: flex;
                gap: 0.25rem;
                margin-bottom: 0.5rem;
            }

            .star {
                font-size: 1.5rem;
                color: var(--gray-300, #d1d5db);
                cursor: pointer;
                transition: color 0.2s ease;
            }

            .star:hover,
            .star.active {
                color: var(--accent, #f59e0b);
            }

            .rating-text {
                font-size: 0.875rem;
                color: var(--text-secondary, #4b5563);
            }

            .review-criteria {
                margin-bottom: 2rem;
            }

            .criteria-item {
                margin-bottom: 1.5rem;
            }

            #review-text {
                width: 100%;
                padding: 1rem;
                border: 1px solid var(--border, #e5e7eb);
                border-radius: var(--radius-md, 12px);
                font-family: inherit;
                resize: vertical;
                min-height: 120px;
            }

            .recommendation-buttons {
                display: flex;
                gap: 1rem;
                margin-top: 0.5rem;
            }

            .rec-btn {
                flex: 1;
                padding: 0.75rem 1rem;
                border: 2px solid var(--border, #e5e7eb);
                background: var(--surface, #f9fafb);
                border-radius: var(--radius-md, 12px);
                cursor: pointer;
                transition: all 0.2s ease;
                font-weight: 500;
            }

            .rec-btn:hover {
                transform: translateY(-1px);
                box-shadow: var(--shadow-md, 0 4px 6px -1px rgb(0 0 0 / 0.1));
            }

            .rec-btn.active {
                border-color: var(--primary, #6366f1);
                background: var(--primary-bg, #eef2ff);
                color: var(--primary-dark, #4f46e5);
            }

            .review-actions {
                display: flex;
                gap: 1rem;
                margin-top: 2rem;
                padding-top: 1.5rem;
                border-top: 1px solid var(--border, #e5e7eb);
            }

            .review-btn {
                flex: 1;
                padding: 0.75rem 1.5rem;
                border-radius: var(--radius-md, 12px);
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                border: none;
            }

            .review-btn.primary {
                background: var(--primary, #6366f1);
                color: white;
            }

            .review-btn.primary:hover {
                background: var(--primary-dark, #4f46e5);
            }

            .review-btn.secondary {
                background: var(--gray-200, #e5e7eb);
                color: var(--text-primary, #111827);
            }

            .review-btn.secondary:hover {
                background: var(--gray-300, #d1d5db);
            }

            .voting-section {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem;
                background: var(--surface, #f9fafb);
                border-radius: var(--radius-lg, 16px);
                border: 1px solid var(--border, #e5e7eb);
                margin-top: 1rem;
            }

            .vote-btn {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                border: 2px solid var(--border, #e5e7eb);
                background: var(--background, #ffffff);
                border-radius: var(--radius-md, 12px);
                cursor: pointer;
                transition: all 0.2s ease;
                font-weight: 500;
                font-size: 0.875rem;
            }

            .vote-btn:hover {
                transform: translateY(-1px);
                box-shadow: var(--shadow-sm, 0 1px 2px 0 rgb(0 0 0 / 0.05));
            }

            .vote-btn.upvote.active {
                border-color: var(--success, #10b981);
                background: #ecfdf5;
                color: var(--success, #10b981);
            }

            .vote-btn.downvote.active {
                border-color: var(--error, #ef4444);
                background: #fef2f2;
                color: var(--error, #ef4444);
            }

            .vote-count {
                font-weight: 600;
                color: var(--text-primary, #111827);
            }

            .vote-summary {
                margin-left: auto;
                font-size: 0.875rem;
                color: var(--text-secondary, #4b5563);
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(modal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeReview();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                this.closeReview();
            }
        });
    }

    openReview(projectId, reviewType = 'idea') {
        const dataManager = window.ProjectDataManager;
        const project = dataManager.getProject(projectId);
        
        if (!project) {
            console.error('Project not found:', projectId);
            return;
        }

        this.currentProject = project;
        this.currentReviewType = reviewType;

        // Update modal content
        document.getElementById('review-title').textContent = `Review: ${reviewType.charAt(0).toUpperCase() + reviewType.slice(1)}`;
        document.getElementById('review-project-info').innerHTML = `
            <strong>${project.title}</strong><br>
            <span style="color: var(--text-secondary);">${project.field} • ${project.status}</span>
        `;
        
        document.getElementById('review-type').value = reviewType;
        this.updateReviewForm();
        this.resetForm();

        document.getElementById('review-modal').classList.add('show');
    }

    updateReviewForm() {
        const reviewType = document.getElementById('review-type').value;
        const criteriaContainer = document.getElementById('review-criteria');
        
        const criteriaByType = {
            idea: [
                { id: 'novelty', label: 'Novelty & Innovation' },
                { id: 'feasibility', label: 'Technical Feasibility' },
                { id: 'impact', label: 'Potential Impact' },
                { id: 'clarity', label: 'Problem Definition' }
            ],
            design: [
                { id: 'methodology', label: 'Methodology Soundness' },
                { id: 'completeness', label: 'Design Completeness' },
                { id: 'feasibility', label: 'Technical Feasibility' },
                { id: 'timeline', label: 'Timeline Realism' }
            ],
            implementation: [
                { id: 'detail', label: 'Implementation Detail' },
                { id: 'milestones', label: 'Milestone Definition' },
                { id: 'resources', label: 'Resource Planning' },
                { id: 'risks', label: 'Risk Assessment' }
            ],
            code: [
                { id: 'quality', label: 'Code Quality' },
                { id: 'documentation', label: 'Documentation' },
                { id: 'testing', label: 'Test Coverage' },
                { id: 'reproducibility', label: 'Reproducibility' }
            ],
            data: [
                { id: 'quality', label: 'Data Quality' },
                { id: 'documentation', label: 'Data Documentation' },
                { id: 'ethics', label: 'Ethics & Privacy' },
                { id: 'accessibility', label: 'Data Accessibility' }
            ],
            paper: [
                { id: 'methodology', label: 'Methodology' },
                { id: 'results', label: 'Results & Analysis' },
                { id: 'writing', label: 'Writing Quality' },
                { id: 'significance', label: 'Scientific Significance' }
            ]
        };

        const criteria = criteriaByType[reviewType] || [];
        
        criteriaContainer.innerHTML = criteria.map(criterion => `
            <div class="criteria-item">
                <label class="review-label">${criterion.label}</label>
                <div class="rating-stars" id="${criterion.id}-rating">
                    ${[1,2,3,4,5].map(i => `
                        <span class="star" data-rating="${i}" onclick="reviewSystem.setRating('${criterion.id}', ${i})">★</span>
                    `).join('')}
                </div>
                <span class="rating-text" id="${criterion.id}-rating-text">No rating</span>
            </div>
        `).join('');
    }

    setRating(criterionId, rating) {
        const stars = document.querySelectorAll(`#${criterionId}-rating .star`);
        const ratingText = document.getElementById(`${criterionId}-rating-text`);
        
        stars.forEach((star, index) => {
            star.classList.toggle('active', index < rating);
        });
        
        const labels = ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'];
        ratingText.textContent = `${rating}/5 - ${labels[rating - 1]}`;
        
        // Store rating
        if (!this.currentRatings) this.currentRatings = {};
        this.currentRatings[criterionId] = rating;
    }

    setRecommendation(recommendation) {
        document.querySelectorAll('.rec-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.querySelector(`[data-rec="${recommendation}"]`).classList.add('active');
        document.getElementById('recommendation').value = recommendation;
    }

    submitReview(event) {
        event.preventDefault();
        
        const reviewData = {
            projectId: this.currentProject.id,
            type: document.getElementById('review-type').value,
            ratings: this.currentRatings || {},
            text: document.getElementById('review-text').value,
            recommendation: document.getElementById('recommendation').value,
            reviewer: 'current-user', // In real app, get from auth
            date: new Date().toISOString(),
            id: `review-${Date.now()}`
        };

        // Calculate overall score
        const ratingValues = Object.values(reviewData.ratings);
        reviewData.overallScore = ratingValues.length > 0 
            ? ratingValues.reduce((a, b) => a + b, 0) / ratingValues.length 
            : 0;

        // Store review
        this.saveReview(reviewData);
        
        // Show success message
        this.showSuccessMessage('Review submitted successfully!');
        
        // Close modal
        this.closeReview();
        
        // Refresh page to show new review
        if (typeof window.location !== 'undefined') {
            setTimeout(() => window.location.reload(), 1000);
        }
    }

    saveReview(reviewData) {
        if (!this.reviews[reviewData.projectId]) {
            this.reviews[reviewData.projectId] = [];
        }
        this.reviews[reviewData.projectId].push(reviewData);
        
        // Save to localStorage
        localStorage.setItem('llmxive-reviews', JSON.stringify(this.reviews));
        
        console.log('Review saved:', reviewData);
    }

    loadReviews() {
        try {
            const stored = localStorage.getItem('llmxive-reviews');
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            console.error('Failed to load reviews:', error);
            return {};
        }
    }

    getProjectReviews(projectId) {
        return this.reviews[projectId] || [];
    }

    vote(projectId, voteType) {
        if (!this.votes[projectId]) {
            this.votes[projectId] = { upvotes: 0, downvotes: 0, userVote: null };
        }

        const projectVotes = this.votes[projectId];
        const previousVote = projectVotes.userVote;

        // Remove previous vote
        if (previousVote === 'up') projectVotes.upvotes--;
        if (previousVote === 'down') projectVotes.downvotes--;

        // Add new vote (or toggle off if same)
        if (previousVote !== voteType) {
            if (voteType === 'up') projectVotes.upvotes++;
            if (voteType === 'down') projectVotes.downvotes++;
            projectVotes.userVote = voteType;
        } else {
            projectVotes.userVote = null;
        }

        // Save votes
        localStorage.setItem('llmxive-votes', JSON.stringify(this.votes));
        
        // Update UI
        this.updateVoteDisplay(projectId);
        
        return projectVotes;
    }

    loadVotes() {
        try {
            const stored = localStorage.getItem('llmxive-votes');
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            console.error('Failed to load votes:', error);
            return {};
        }
    }

    getProjectVotes(projectId) {
        return this.votes[projectId] || { upvotes: 0, downvotes: 0, userVote: null };
    }

    updateVoteDisplay(projectId) {
        const votes = this.getProjectVotes(projectId);
        const upvoteBtn = document.querySelector(`[data-project="${projectId}"] .vote-btn.upvote`);
        const downvoteBtn = document.querySelector(`[data-project="${projectId}"] .vote-btn.downvote`);
        
        if (upvoteBtn) {
            upvoteBtn.classList.toggle('active', votes.userVote === 'up');
            upvoteBtn.querySelector('.vote-count').textContent = votes.upvotes;
        }
        
        if (downvoteBtn) {
            downvoteBtn.classList.toggle('active', votes.userVote === 'down');
            downvoteBtn.querySelector('.vote-count').textContent = votes.downvotes;
        }
    }

    resetForm() {
        this.currentRatings = {};
        document.getElementById('review-text').value = '';
        document.getElementById('recommendation').value = '';
        
        // Reset all stars
        document.querySelectorAll('.star').forEach(star => star.classList.remove('active'));
        document.querySelectorAll('.rating-text').forEach(text => text.textContent = 'No rating');
        document.querySelectorAll('.rec-btn').forEach(btn => btn.classList.remove('active'));
    }

    closeReview() {
        document.getElementById('review-modal').classList.remove('show');
    }

    showSuccessMessage(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success, #10b981);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md, 12px);
            box-shadow: var(--shadow-lg, 0 10px 15px -3px rgb(0 0 0 / 0.1));
            z-index: 9999;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Create global instance
window.reviewSystem = window.reviewSystem || new ReviewSystem();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReviewSystem;
}

console.log('📝 ReviewSystem loaded');