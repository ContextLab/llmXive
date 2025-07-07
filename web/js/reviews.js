/**
 * Reviews Manager for llmXive
 * Handles review workflow, submission, and management
 */

import { EventTarget } from './events.js';
import { DateUtils, StringUtils, ValidationUtils, DOMUtils } from './utils.js';

export class ReviewsManager extends EventTarget {
    constructor(client, notifications) {
        super();
        
        this.client = client;
        this.notifications = notifications;
        this.reviews = [];
        this.filteredReviews = [];
        this.currentFilters = {
            type: '',
            status: '',
            project: '',
            reviewer: '',
            search: ''
        };
        this.selectedReview = null;
        this.unsavedChanges = false;
        
        // Bind methods
        this.handleFilterChange = this.handleFilterChange.bind(this);
        this.handleSearchInput = this.handleSearchInput.bind(this);
        this.handleReviewClick = this.handleReviewClick.bind(this);
        this.handleReviewAction = this.handleReviewAction.bind(this);
        this.handleNewReview = this.handleNewReview.bind(this);
        
        // Debounced search
        this.debouncedSearch = DOMUtils.debounce(this.performSearch.bind(this), 300);
    }
    
    /**
     * Load reviews page
     */
    async load() {
        try {
            console.log('Loading reviews...');
            
            // Show loading state
            this.showLoadingState();
            
            // Load reviews data
            await this.loadReviews();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Apply initial filters
            this.applyFilters();
            
            console.log('Reviews page loaded successfully');
            
        } catch (error) {
            console.error('Failed to load reviews:', error);
            this.showErrorState(error.message);
        }
    }
    
    /**
     * Load reviews from API
     */
    async loadReviews() {
        try {
            console.log('Fetching reviews...');
            
            // TODO: Replace with actual API call
            this.reviews = await this.fetchReviews();
            this.filteredReviews = [...this.reviews];
            
            this.renderReviews();
            
        } catch (error) {
            console.error('Failed to fetch reviews:', error);
            throw error;
        }
    }
    
    /**
     * Fetch reviews from API (mock implementation)
     */
    async fetchReviews() {
        // TODO: Replace with actual API calls
        return new Promise(resolve => {
            setTimeout(() => {
                const mockReviews = [
                    {
                        id: 'rev-001',
                        title: 'Technical Design Review - AI Safety Framework',
                        type: 'design',
                        status: 'completed',
                        projectId: 'proj-001',
                        projectTitle: 'AI Safety Research Framework',
                        reviewer: {
                            type: 'automated',
                            name: 'Claude-3',
                            avatar: null
                        },
                        score: 85,
                        points: 0.5,
                        summary: 'Comprehensive technical design with well-defined architecture. Minor concerns about scalability.',
                        strengths: [
                            'Clear system architecture',
                            'Well-documented APIs',
                            'Proper error handling'
                        ],
                        concerns: [
                            'Database scaling considerations',
                            'Missing load testing plan'
                        ],
                        recommendations: [
                            'Add horizontal scaling strategy',
                            'Implement caching layer'
                        ],
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
                        completedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1), // 1 day ago
                        tags: ['design', 'architecture', 'ai-safety']
                    },
                    {
                        id: 'rev-002',
                        title: 'Code Review - Quantum Algorithm Implementation',
                        type: 'code',
                        status: 'in_progress',
                        projectId: 'proj-002',
                        projectTitle: 'Quantum Computing Applications',
                        reviewer: {
                            type: 'manual',
                            name: 'alice',
                            avatar: null
                        },
                        score: null,
                        points: 1.0,
                        summary: 'Currently reviewing quantum circuit optimization algorithms.',
                        strengths: [],
                        concerns: [],
                        recommendations: [],
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 12), // 12 hours ago
                        completedAt: null,
                        tags: ['code', 'quantum', 'algorithms']
                    },
                    {
                        id: 'rev-003',
                        title: 'Paper Review - Neural Network Optimization Methods',
                        type: 'paper',
                        status: 'pending',
                        projectId: 'proj-003',
                        projectTitle: 'Neural Network Optimization',
                        reviewer: {
                            type: 'automated',
                            name: 'GPT-4',
                            avatar: null
                        },
                        score: null,
                        points: 0.5,
                        summary: 'Queued for automated review generation.',
                        strengths: [],
                        concerns: [],
                        recommendations: [],
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
                        completedAt: null,
                        tags: ['paper', 'neural-networks', 'optimization']
                    },
                    {
                        id: 'rev-004',
                        title: 'Implementation Review - Data Pipeline Architecture',
                        type: 'implementation',
                        status: 'completed',
                        projectId: 'proj-001',
                        projectTitle: 'AI Safety Research Framework',
                        reviewer: {
                            type: 'manual',
                            name: 'bob',
                            avatar: null
                        },
                        score: 92,
                        points: 1.0,
                        summary: 'Excellent implementation with robust error handling and monitoring.',
                        strengths: [
                            'Comprehensive logging',
                            'Proper data validation',
                            'Efficient processing pipeline'
                        ],
                        concerns: [
                            'Memory usage could be optimized'
                        ],
                        recommendations: [
                            'Implement data streaming',
                            'Add memory profiling'
                        ],
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5), // 5 days ago
                        completedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), // 3 days ago
                        tags: ['implementation', 'data-pipeline', 'architecture']
                    }
                ];
                resolve(mockReviews);
            }, 600);
        });
    }
    
    /**
     * Render reviews list
     */
    renderReviews() {
        const reviewsList = document.getElementById('reviews-list');
        if (!reviewsList) return;
        
        if (this.filteredReviews.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const reviewsHtml = this.filteredReviews.map(review => 
            this.renderReviewCard(review)
        ).join('');
        
        reviewsList.innerHTML = reviewsHtml;
        
        // Set up review card listeners
        this.setupReviewCardListeners();
    }
    
    /**
     * Render individual review card
     */
    renderReviewCard(review) {
        const statusClass = review.status.replace('_', '-');
        const typeIcon = this.getTypeIcon(review.type);
        const reviewerLabel = review.reviewer.type === 'automated' ? 
            `🤖 ${review.reviewer.name}` : 
            `👤 ${review.reviewer.name}`;
        
        const scoreHtml = review.score !== null ? 
            `<div class="review-score score-${this.getScoreClass(review.score)}">${review.score}</div>` :
            '<div class="review-score pending">-</div>';
        
        const progressHtml = review.status === 'completed' ?
            `<div class="review-completed">
                <i class="fas fa-check-circle"></i>
                Completed ${DateUtils.formatRelative(review.completedAt)}
            </div>` :
            review.status === 'in_progress' ?
            `<div class="review-progress">
                <i class="fas fa-clock"></i>
                In Progress
            </div>` :
            `<div class="review-pending">
                <i class="fas fa-hourglass-half"></i>
                Pending Review
            </div>`;
        
        return `
            <div class="review-card ${statusClass}" data-review-id="${review.id}">
                <div class="review-header">
                    <div class="review-type">
                        <i class="${typeIcon}"></i>
                        <span>${StringUtils.capitalize(review.type)} Review</span>
                    </div>
                    ${scoreHtml}
                </div>
                
                <div class="review-content">
                    <h3 class="review-title">${review.title}</h3>
                    <p class="review-project">
                        <i class="fas fa-folder"></i>
                        ${review.projectTitle}
                    </p>
                    
                    <div class="review-summary">
                        ${review.summary}
                    </div>
                    
                    <div class="review-details">
                        <div class="review-points">
                            <span class="review-points-value">${review.points}</span>
                            <span class="review-points-label">points</span>
                        </div>
                        
                        <div class="review-reviewer">
                            ${reviewerLabel}
                        </div>
                    </div>
                </div>
                
                <div class="review-footer">
                    <div class="review-meta">
                        ${progressHtml}
                        <div class="review-created">
                            Created ${DateUtils.formatRelative(review.createdAt)}
                        </div>
                    </div>
                    
                    <div class="review-actions">
                        <button class="review-action" data-action="view" title="View review">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${review.status === 'pending' ? 
                            `<button class="review-action" data-action="approve" title="Approve review">
                                <i class="fas fa-check"></i>
                            </button>` : ''
                        }
                        <button class="review-action" data-action="more" title="More options">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Get icon for review type
     */
    getTypeIcon(type) {
        const icons = {
            design: 'fas fa-drafting-compass',
            implementation: 'fas fa-code',
            paper: 'fas fa-file-alt',
            code: 'fas fa-code-branch'
        };
        return icons[type] || 'fas fa-clipboard-list';
    }
    
    /**
     * Get CSS class for score
     */
    getScoreClass(score) {
        if (score >= 90) return 'excellent';
        if (score >= 80) return 'good';
        if (score >= 70) return 'fair';
        return 'poor';
    }
    
    /**
     * Show empty state when no reviews match filters
     */
    showEmptyState() {
        const reviewsList = document.getElementById('reviews-list');
        if (!reviewsList) return;
        
        const hasActiveFilters = Object.values(this.currentFilters).some(filter => filter !== '');
        
        if (hasActiveFilters) {
            reviewsList.innerHTML = `
                <div class="reviews-empty">
                    <i class="fas fa-search"></i>
                    <h3>No Reviews Found</h3>
                    <p>No reviews match your current filters. Try adjusting your search criteria.</p>
                    <button class="btn btn-secondary" id="clear-filters-btn">
                        Clear Filters
                    </button>
                </div>
            `;
            
            // Set up clear filters listener
            const clearBtn = document.getElementById('clear-filters-btn');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => this.clearFilters());
            }
        } else {
            reviewsList.innerHTML = `
                <div class="reviews-empty">
                    <i class="fas fa-clipboard-list"></i>
                    <h3>No Reviews Yet</h3>
                    <p>Reviews will appear here as they are generated or submitted. Start by creating a project or requesting a review.</p>
                    <div class="reviews-empty-actions">
                        <button class="btn btn-primary" id="create-project-btn">
                            <i class="fas fa-plus"></i>
                            Create Project
                        </button>
                        <button class="btn btn-secondary" id="request-review-btn">
                            <i class="fas fa-clipboard-check"></i>
                            Request Review
                        </button>
                    </div>
                </div>
            `;
            
            // Set up action listeners
            const createBtn = document.getElementById('create-project-btn');
            const requestBtn = document.getElementById('request-review-btn');
            
            if (createBtn) {
                createBtn.addEventListener('click', () => {
                    this.emit('navigate', { page: 'projects', action: 'create' });
                });
            }
            
            if (requestBtn) {
                requestBtn.addEventListener('click', this.handleNewReview);
            }
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        const reviewsList = document.getElementById('reviews-list');
        if (!reviewsList) return;
        
        const skeletonCards = Array.from({ length: 4 }, (_, i) => `
            <div class="review-skeleton" style="--index: ${i}"></div>
        `).join('');
        
        reviewsList.innerHTML = skeletonCards;
    }
    
    /**
     * Show error state
     */
    showErrorState(message) {
        const reviewsList = document.getElementById('reviews-list');
        if (!reviewsList) return;
        
        reviewsList.innerHTML = `
            <div class="reviews-empty">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Failed to Load Reviews</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="window.location.reload()">
                    <i class="fas fa-sync-alt"></i>
                    Retry
                </button>
            </div>
        `;
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Filter controls
        const typeFilter = document.getElementById('type-filter');
        const statusFilter = document.getElementById('status-filter');
        const projectFilter = document.getElementById('project-filter');
        const reviewerFilter = document.getElementById('reviewer-filter');
        const searchInput = document.getElementById('review-search');
        const newReviewBtn = document.getElementById('new-review-btn');
        
        [typeFilter, statusFilter, projectFilter, reviewerFilter].forEach(filter => {
            if (filter) {
                filter.removeEventListener('change', this.handleFilterChange);
                filter.addEventListener('change', this.handleFilterChange);
            }
        });
        
        if (searchInput) {
            searchInput.removeEventListener('input', this.handleSearchInput);
            searchInput.addEventListener('input', this.handleSearchInput);
        }
        
        if (newReviewBtn) {
            newReviewBtn.removeEventListener('click', this.handleNewReview);
            newReviewBtn.addEventListener('click', this.handleNewReview);
        }
    }
    
    /**
     * Set up review card event listeners
     */
    setupReviewCardListeners() {
        // Review card clicks
        const reviewCards = document.querySelectorAll('.review-card');
        reviewCards.forEach(card => {
            card.removeEventListener('click', this.handleReviewClick);
            card.addEventListener('click', this.handleReviewClick);
        });
        
        // Review action buttons
        const actionButtons = document.querySelectorAll('.review-action');
        actionButtons.forEach(button => {
            button.removeEventListener('click', this.handleReviewAction);
            button.addEventListener('click', this.handleReviewAction);
        });
    }
    
    /**
     * Handle filter changes
     */
    handleFilterChange(event) {
        const filterType = event.target.id.replace('-filter', '');
        this.currentFilters[filterType] = event.target.value;
        
        this.applyFilters();
    }
    
    /**
     * Handle search input
     */
    handleSearchInput(event) {
        this.currentFilters.search = event.target.value;
        this.debouncedSearch();
    }
    
    /**
     * Perform search
     */
    performSearch() {
        this.applyFilters();
    }
    
    /**
     * Apply current filters to reviews
     */
    applyFilters() {
        this.filteredReviews = this.reviews.filter(review => {
            // Type filter
            if (this.currentFilters.type && review.type !== this.currentFilters.type) {
                return false;
            }
            
            // Status filter
            if (this.currentFilters.status && review.status !== this.currentFilters.status) {
                return false;
            }
            
            // Project filter
            if (this.currentFilters.project && review.projectId !== this.currentFilters.project) {
                return false;
            }
            
            // Reviewer filter
            if (this.currentFilters.reviewer) {
                if (this.currentFilters.reviewer === 'automated' && review.reviewer.type !== 'automated') {
                    return false;
                }
                if (this.currentFilters.reviewer === 'manual' && review.reviewer.type !== 'manual') {
                    return false;
                }
            }
            
            // Search filter
            if (this.currentFilters.search) {
                const searchLower = this.currentFilters.search.toLowerCase();
                const matchesTitle = review.title.toLowerCase().includes(searchLower);
                const matchesProject = review.projectTitle.toLowerCase().includes(searchLower);
                const matchesSummary = review.summary.toLowerCase().includes(searchLower);
                const matchesTags = review.tags.some(tag => tag.toLowerCase().includes(searchLower));
                
                if (!matchesTitle && !matchesProject && !matchesSummary && !matchesTags) {
                    return false;
                }
            }
            
            return true;
        });
        
        this.renderReviews();
        
        // Update URL with current filters
        this.updateURLFilters();
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.currentFilters = {
            type: '',
            status: '',
            project: '',
            reviewer: '',
            search: ''
        };
        
        // Update filter controls
        const typeFilter = document.getElementById('type-filter');
        const statusFilter = document.getElementById('status-filter');
        const projectFilter = document.getElementById('project-filter');
        const reviewerFilter = document.getElementById('reviewer-filter');
        const searchInput = document.getElementById('review-search');
        
        if (typeFilter) typeFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        if (projectFilter) projectFilter.value = '';
        if (reviewerFilter) reviewerFilter.value = '';
        if (searchInput) searchInput.value = '';
        
        this.applyFilters();
    }
    
    /**
     * Handle review card click
     */
    handleReviewClick(event) {
        // Don't trigger if clicking on action buttons
        if (event.target.closest('.review-action')) {
            return;
        }
        
        const card = event.target.closest('.review-card');
        const reviewId = card.dataset.reviewId;
        const review = this.reviews.find(r => r.id === reviewId);
        
        if (review) {
            this.showReviewDetails(review);
        }
    }
    
    /**
     * Handle review action buttons
     */
    handleReviewAction(event) {
        event.stopPropagation();
        
        const button = event.target.closest('.review-action');
        const action = button.dataset.action;
        const card = button.closest('.review-card');
        const reviewId = card.dataset.reviewId;
        const review = this.reviews.find(r => r.id === reviewId);
        
        switch (action) {
            case 'view':
                this.showReviewDetails(review);
                break;
            case 'approve':
                this.approveReview(review);
                break;
            case 'more':
                this.showReviewMenu(review, button);
                break;
        }
    }
    
    /**
     * Handle new review button
     */
    handleNewReview(event) {
        event.preventDefault();
        this.createNewReview();
    }
    
    /**
     * Show review details modal
     */
    showReviewDetails(review) {
        console.log('Showing review details for:', review.title);
        
        // TODO: Implement review details modal
        this.notifications.info(`Review details for "${review.title}" - Coming soon!`);
        
        this.selectedReview = review;
        this.emit('reviewSelected', { review });
    }
    
    /**
     * Approve review
     */
    async approveReview(review) {
        try {
            // TODO: Call API to approve review
            
            this.notifications.success(`Review "${review.title}" approved`);
            
            // Update local state
            review.status = 'completed';
            review.completedAt = new Date();
            
            this.renderReviews();
            
        } catch (error) {
            console.error('Failed to approve review:', error);
            this.notifications.error('Failed to approve review');
        }
    }
    
    /**
     * Show review context menu
     */
    showReviewMenu(review, button) {
        // TODO: Implement review context menu
        console.log('Show menu for review:', review.title);
    }
    
    /**
     * Create new review
     */
    createNewReview() {
        console.log('Creating new review...');
        
        // TODO: Implement review creation modal
        this.notifications.info('Create new review - Coming soon!');
        
        this.emit('reviewCreate');
    }
    
    /**
     * Update URL with current filters
     */
    updateURLFilters() {
        const params = new URLSearchParams();
        
        Object.entries(this.currentFilters).forEach(([key, value]) => {
            if (value) {
                params.set(key, value);
            }
        });
        
        const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}${window.location.hash}`;
        window.history.replaceState(null, '', newUrl);
    }
    
    /**
     * Load filters from URL
     */
    loadFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);
        
        this.currentFilters.type = params.get('type') || '';
        this.currentFilters.status = params.get('status') || '';
        this.currentFilters.project = params.get('project') || '';
        this.currentFilters.reviewer = params.get('reviewer') || '';
        this.currentFilters.search = params.get('search') || '';
        
        // Update filter controls
        const typeFilter = document.getElementById('type-filter');
        const statusFilter = document.getElementById('status-filter');
        const projectFilter = document.getElementById('project-filter');
        const reviewerFilter = document.getElementById('reviewer-filter');
        const searchInput = document.getElementById('review-search');
        
        if (typeFilter) typeFilter.value = this.currentFilters.type;
        if (statusFilter) statusFilter.value = this.currentFilters.status;
        if (projectFilter) projectFilter.value = this.currentFilters.project;
        if (reviewerFilter) reviewerFilter.value = this.currentFilters.reviewer;
        if (searchInput) searchInput.value = this.currentFilters.search;
    }
    
    /**
     * Check for unsaved changes
     */
    hasUnsavedChanges() {
        return this.unsavedChanges;
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        // Remove event listeners
        const typeFilter = document.getElementById('type-filter');
        const statusFilter = document.getElementById('status-filter');
        const projectFilter = document.getElementById('project-filter');
        const reviewerFilter = document.getElementById('reviewer-filter');
        const searchInput = document.getElementById('review-search');
        const newReviewBtn = document.getElementById('new-review-btn');
        
        [typeFilter, statusFilter, projectFilter, reviewerFilter].forEach(filter => {
            if (filter) {
                filter.removeEventListener('change', this.handleFilterChange);
            }
        });
        
        if (searchInput) {
            searchInput.removeEventListener('input', this.handleSearchInput);
        }
        if (newReviewBtn) {
            newReviewBtn.removeEventListener('click', this.handleNewReview);
        }
        
        // Clear data
        this.reviews = [];
        this.filteredReviews = [];
        this.selectedReview = null;
        this.unsavedChanges = false;
        
        console.log('Reviews manager cleaned up');
    }
}

export default ReviewsManager;