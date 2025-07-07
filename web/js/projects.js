/**
 * Projects Manager for llmXive
 * Handles project listing, creation, editing, and management
 */

import { EventTarget } from './events.js';
import { DateUtils, StringUtils, DOMUtils, ValidationUtils } from './utils.js';

export class ProjectsManager extends EventTarget {
    constructor(client, notifications) {
        super();
        
        this.client = client;
        this.notifications = notifications;
        this.projects = [];
        this.filteredProjects = [];
        this.currentFilters = {
            status: '',
            phase: '',
            search: ''
        };
        this.selectedProject = null;
        this.unsavedChanges = false;
        
        // Bind methods
        this.handleFilterChange = this.handleFilterChange.bind(this);
        this.handleSearchInput = this.handleSearchInput.bind(this);
        this.handleProjectClick = this.handleProjectClick.bind(this);
        this.handleNewProject = this.handleNewProject.bind(this);
        this.handleProjectAction = this.handleProjectAction.bind(this);
        
        // Debounced search
        this.debouncedSearch = DOMUtils.debounce(this.performSearch.bind(this), 300);
    }
    
    /**
     * Load projects page
     */
    async load() {
        try {
            console.log('Loading projects...');
            
            // Show loading state
            this.showLoadingState();
            
            // Load projects data
            await this.loadProjects();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Apply initial filters
            this.applyFilters();
            
            console.log('Projects page loaded successfully');
            
        } catch (error) {
            console.error('Failed to load projects:', error);
            this.showErrorState(error.message);
        }
    }
    
    /**
     * Load projects from API
     */
    async loadProjects() {
        try {
            console.log('Fetching projects...');
            
            // TODO: Replace with actual API call
            this.projects = await this.fetchProjects();
            this.filteredProjects = [...this.projects];
            
            this.renderProjects();
            
        } catch (error) {
            console.error('Failed to fetch projects:', error);
            throw error;
        }
    }
    
    /**
     * Fetch projects from API (mock implementation)
     */
    async fetchProjects() {
        // TODO: Replace with actual API calls
        return new Promise(resolve => {
            setTimeout(() => {
                const mockProjects = [
                    {
                        id: 'proj-001',
                        title: 'AI Safety Research Framework',
                        description: 'Developing comprehensive methodologies for AI safety evaluation and testing in real-world scenarios.',
                        phase: 'implementation',
                        status: 'active',
                        progress: 75,
                        contributors: [
                            { username: 'alice', name: 'Alice Smith', avatar: null },
                            { username: 'bob', name: 'Bob Johnson', avatar: null }
                        ],
                        stats: {
                            reviews: 12,
                            commits: 45,
                            citations: 8
                        },
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30), // 30 days ago
                        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
                        tags: ['ai-safety', 'research', 'framework']
                    },
                    {
                        id: 'proj-002',
                        title: 'Quantum Computing Applications',
                        description: 'Exploring quantum algorithms for optimization problems in scientific computing.',
                        phase: 'paper',
                        status: 'active',
                        progress: 90,
                        contributors: [
                            { username: 'charlie', name: 'Charlie Wilson', avatar: null }
                        ],
                        stats: {
                            reviews: 8,
                            commits: 23,
                            citations: 15
                        },
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60), // 60 days ago
                        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 12), // 12 hours ago
                        tags: ['quantum', 'optimization', 'algorithms']
                    },
                    {
                        id: 'proj-003',
                        title: 'Neural Network Optimization',
                        description: 'Novel approaches to training efficiency in deep learning architectures.',
                        phase: 'design',
                        status: 'blocked',
                        progress: 35,
                        contributors: [
                            { username: 'diana', name: 'Diana Lee', avatar: null },
                            { username: 'eve', name: 'Eve Brown', avatar: null },
                            { username: 'frank', name: 'Frank Davis', avatar: null }
                        ],
                        stats: {
                            reviews: 5,
                            commits: 12,
                            citations: 3
                        },
                        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14), // 14 days ago
                        updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
                        tags: ['neural-networks', 'optimization', 'deep-learning']
                    }
                ];
                resolve(mockProjects);
            }, 800);
        });
    }
    
    /**
     * Render projects grid
     */
    renderProjects() {
        const projectsGrid = document.getElementById('projects-grid');
        if (!projectsGrid) return;
        
        if (this.filteredProjects.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const projectsHtml = this.filteredProjects.map(project => 
            this.renderProjectCard(project)
        ).join('');
        
        // Add create new project card
        const createCardHtml = this.renderCreateProjectCard();
        
        projectsGrid.innerHTML = createCardHtml + projectsHtml;
        
        // Set up project card listeners
        this.setupProjectCardListeners();
    }
    
    /**
     * Render individual project card
     */
    renderProjectCard(project) {
        const progressPercentage = Math.round(project.progress || 0);
        const contributorAvatars = project.contributors.slice(0, 3).map(contributor => {
            return contributor.avatar ? 
                `<img src="${contributor.avatar}" alt="${contributor.name}" class="contributor-avatar" title="${contributor.name}">` :
                `<div class="contributor-avatar" title="${contributor.name}">${contributor.name.charAt(0)}</div>`;
        }).join('');
        
        const moreContributors = project.contributors.length > 3 ? 
            `<span class="contributor-count">+${project.contributors.length - 3}</span>` : '';
        
        return `
            <div class="project-card" data-project-id="${project.id}">
                <div class="project-header">
                    <h3 class="project-title">${StringUtils.capitalize(project.title)}</h3>
                    <p class="project-description">${project.description}</p>
                </div>
                
                <div class="project-meta">
                    <div class="project-badges">
                        <span class="project-phase ${project.phase}">${StringUtils.capitalize(project.phase)}</span>
                        <span class="project-status ${project.status}">${StringUtils.capitalize(project.status)}</span>
                    </div>
                    
                    <div class="project-progress">
                        <div class="project-progress-label">
                            <span>Progress</span>
                            <span>${progressPercentage}%</span>
                        </div>
                        <div class="project-progress-bar">
                            <div class="project-progress-fill" style="width: ${progressPercentage}%"></div>
                        </div>
                    </div>
                    
                    <div class="project-stats">
                        <div class="project-stat">
                            <span class="project-stat-value">${project.stats.reviews}</span>
                            <span class="project-stat-label">Reviews</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-value">${project.stats.commits}</span>
                            <span class="project-stat-label">Commits</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-value">${project.stats.citations}</span>
                            <span class="project-stat-label">Citations</span>
                        </div>
                    </div>
                </div>
                
                <div class="project-footer">
                    <div class="project-contributors">
                        <span class="project-contributors-label">Contributors:</span>
                        ${contributorAvatars}
                        ${moreContributors}
                    </div>
                    
                    <div class="project-actions">
                        <button class="project-action favorite" data-action="favorite" title="Add to favorites">
                            <i class="fas fa-star"></i>
                        </button>
                        <button class="project-action" data-action="edit" title="Edit project">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="project-action" data-action="more" title="More options">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                    </div>
                </div>
                
                <div class="project-updated">
                    Last updated ${DateUtils.formatRelative(project.updatedAt)}
                </div>
            </div>
        `;
    }
    
    /**
     * Render create new project card
     */
    renderCreateProjectCard() {
        return `
            <div class="project-create-card" id="create-project-card">
                <div class="project-create-icon">
                    <i class="fas fa-plus"></i>
                </div>
                <h3 class="project-create-title">Create New Project</h3>
                <p class="project-create-description">Start a new research project and collaborate with the community</p>
            </div>
        `;
    }
    
    /**
     * Show empty state when no projects match filters
     */
    showEmptyState() {
        const projectsGrid = document.getElementById('projects-grid');
        if (!projectsGrid) return;
        
        const hasActiveFilters = Object.values(this.currentFilters).some(filter => filter !== '');
        
        if (hasActiveFilters) {
            projectsGrid.innerHTML = `
                <div class="projects-empty">
                    <i class="fas fa-search"></i>
                    <h3>No Projects Found</h3>
                    <p>No projects match your current filters. Try adjusting your search criteria.</p>
                    <button class="btn btn-secondary" onclick="this.closest('.projects-container').querySelector('#project-search').value = ''; this.dispatchEvent(new Event('input', { bubbles: true }))">
                        Clear Filters
                    </button>
                </div>
            `;
        } else {
            projectsGrid.innerHTML = `
                <div class="projects-empty">
                    <i class="fas fa-folder-open"></i>
                    <h3>No Projects Yet</h3>
                    <p>Get started by creating your first research project. Collaborate with the community to advance scientific discovery.</p>
                    <button class="btn btn-primary" id="create-first-project">
                        <i class="fas fa-plus"></i>
                        Create Your First Project
                    </button>
                </div>
            `;
            
            // Set up create first project listener
            const createBtn = document.getElementById('create-first-project');
            if (createBtn) {
                createBtn.addEventListener('click', this.handleNewProject);
            }
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        const projectsGrid = document.getElementById('projects-grid');
        if (!projectsGrid) return;
        
        const skeletonCards = Array.from({ length: 6 }, (_, i) => `
            <div class="project-skeleton" style="--index: ${i}"></div>
        `).join('');
        
        projectsGrid.innerHTML = skeletonCards;
    }
    
    /**
     * Show error state
     */
    showErrorState(message) {
        const projectsGrid = document.getElementById('projects-grid');
        if (!projectsGrid) return;
        
        projectsGrid.innerHTML = `
            <div class="projects-empty">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Failed to Load Projects</h3>
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
        const statusFilter = document.getElementById('status-filter');
        const phaseFilter = document.getElementById('phase-filter');
        const searchInput = document.getElementById('project-search');
        const newProjectBtn = document.getElementById('new-project-btn');
        
        if (statusFilter) {
            statusFilter.removeEventListener('change', this.handleFilterChange);
            statusFilter.addEventListener('change', this.handleFilterChange);
        }
        
        if (phaseFilter) {
            phaseFilter.removeEventListener('change', this.handleFilterChange);
            phaseFilter.addEventListener('change', this.handleFilterChange);
        }
        
        if (searchInput) {
            searchInput.removeEventListener('input', this.handleSearchInput);
            searchInput.addEventListener('input', this.handleSearchInput);
        }
        
        if (newProjectBtn) {
            newProjectBtn.removeEventListener('click', this.handleNewProject);
            newProjectBtn.addEventListener('click', this.handleNewProject);
        }
    }
    
    /**
     * Set up project card event listeners
     */
    setupProjectCardListeners() {
        // Project card clicks
        const projectCards = document.querySelectorAll('.project-card');
        projectCards.forEach(card => {
            card.removeEventListener('click', this.handleProjectClick);
            card.addEventListener('click', this.handleProjectClick);
        });
        
        // Project action buttons
        const actionButtons = document.querySelectorAll('.project-action');
        actionButtons.forEach(button => {
            button.removeEventListener('click', this.handleProjectAction);
            button.addEventListener('click', this.handleProjectAction);
        });
        
        // Create project card
        const createCard = document.getElementById('create-project-card');
        if (createCard) {
            createCard.removeEventListener('click', this.handleNewProject);
            createCard.addEventListener('click', this.handleNewProject);
        }
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
     * Apply current filters to projects
     */
    applyFilters() {
        this.filteredProjects = this.projects.filter(project => {
            // Status filter
            if (this.currentFilters.status && project.status !== this.currentFilters.status) {
                return false;
            }
            
            // Phase filter
            if (this.currentFilters.phase && project.phase !== this.currentFilters.phase) {
                return false;
            }
            
            // Search filter
            if (this.currentFilters.search) {
                const searchLower = this.currentFilters.search.toLowerCase();
                const matchesTitle = project.title.toLowerCase().includes(searchLower);
                const matchesDescription = project.description.toLowerCase().includes(searchLower);
                const matchesTags = project.tags.some(tag => tag.toLowerCase().includes(searchLower));
                
                if (!matchesTitle && !matchesDescription && !matchesTags) {
                    return false;
                }
            }
            
            return true;
        });
        
        this.renderProjects();
        
        // Update URL with current filters
        this.updateURLFilters();
    }
    
    /**
     * Handle project card click
     */
    handleProjectClick(event) {
        // Don't trigger if clicking on action buttons
        if (event.target.closest('.project-action')) {
            return;
        }
        
        const card = event.target.closest('.project-card');
        const projectId = card.dataset.projectId;
        const project = this.projects.find(p => p.id === projectId);
        
        if (project) {
            this.showProjectDetails(project);
        }
    }
    
    /**
     * Handle project action buttons
     */
    handleProjectAction(event) {
        event.stopPropagation();
        
        const button = event.target.closest('.project-action');
        const action = button.dataset.action;
        const card = button.closest('.project-card');
        const projectId = card.dataset.projectId;
        const project = this.projects.find(p => p.id === projectId);
        
        switch (action) {
            case 'favorite':
                this.toggleFavorite(project, button);
                break;
            case 'edit':
                this.editProject(project);
                break;
            case 'more':
                this.showProjectMenu(project, button);
                break;
        }
    }
    
    /**
     * Handle new project button
     */
    handleNewProject(event) {
        event.preventDefault();
        this.createNewProject();
    }
    
    /**
     * Show project details modal
     */
    showProjectDetails(project) {
        console.log('Showing project details for:', project.title);
        
        // TODO: Implement project details modal
        this.notifications.info(`Project details for "${project.title}" - Coming soon!`);
        
        this.selectedProject = project;
        this.emit('projectSelected', { project });
    }
    
    /**
     * Toggle project favorite status
     */
    async toggleFavorite(project, button) {
        try {
            const isFavorited = button.classList.contains('active');
            
            // TODO: Call API to update favorite status
            
            button.classList.toggle('active', !isFavorited);
            
            const message = isFavorited ? 
                `Removed "${project.title}" from favorites` :
                `Added "${project.title}" to favorites`;
                
            this.notifications.success(message);
            
        } catch (error) {
            console.error('Failed to toggle favorite:', error);
            this.notifications.error('Failed to update favorite status');
        }
    }
    
    /**
     * Edit project
     */
    editProject(project) {
        console.log('Editing project:', project.title);
        
        // TODO: Implement project editing
        this.notifications.info(`Edit project "${project.title}" - Coming soon!`);
        
        this.emit('projectEdit', { project });
    }
    
    /**
     * Show project context menu
     */
    showProjectMenu(project, button) {
        // TODO: Implement project context menu
        console.log('Show menu for project:', project.title);
    }
    
    /**
     * Create new project
     */
    createNewProject() {
        console.log('Creating new project...');
        
        // TODO: Implement project creation modal
        this.notifications.info('Create new project - Coming soon!');
        
        this.emit('projectCreate');
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
        
        this.currentFilters.status = params.get('status') || '';
        this.currentFilters.phase = params.get('phase') || '';
        this.currentFilters.search = params.get('search') || '';
        
        // Update filter controls
        const statusFilter = document.getElementById('status-filter');
        const phaseFilter = document.getElementById('phase-filter');
        const searchInput = document.getElementById('project-search');
        
        if (statusFilter) statusFilter.value = this.currentFilters.status;
        if (phaseFilter) phaseFilter.value = this.currentFilters.phase;
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
        const statusFilter = document.getElementById('status-filter');
        const phaseFilter = document.getElementById('phase-filter');
        const searchInput = document.getElementById('project-search');
        const newProjectBtn = document.getElementById('new-project-btn');
        
        if (statusFilter) {
            statusFilter.removeEventListener('change', this.handleFilterChange);
        }
        if (phaseFilter) {
            phaseFilter.removeEventListener('change', this.handleFilterChange);
        }
        if (searchInput) {
            searchInput.removeEventListener('input', this.handleSearchInput);
        }
        if (newProjectBtn) {
            newProjectBtn.removeEventListener('click', this.handleNewProject);
        }
        
        // Clear data
        this.projects = [];
        this.filteredProjects = [];
        this.selectedProject = null;
        this.unsavedChanges = false;
        
        console.log('Projects manager cleaned up');
    }
}

export default ProjectsManager;