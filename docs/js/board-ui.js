// Board UI with proper columns
class BoardUI {
    constructor() {
        this.projectsContainer = document.getElementById('projectsGrid');
        this.searchInput = document.getElementById('searchInput');
        this.submitForm = document.getElementById('submitForm');
        
        this.projects = [];
        this.filteredProjects = [];
        this.columns = ['Backlog', 'Ready', 'In Progress', 'In Review'];
        
        this.initializeEventListeners();
        this.renderColumns();
    }
    
    // Initialize event listeners
    initializeEventListeners() {
        // Search with debounce
        let searchTimeout;
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filterProjects();
            }, 300);
        });
        
        // Sort dropdown
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortProjects(e.target.value);
            });
        }
        
        // Submit form
        this.submitForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Submit button
        document.querySelector('a[href="#submit"]').addEventListener('click', (e) => {
            e.preventDefault();
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                this.showSubmitModal();
            } else {
                window.githubAuth.login();
            }
        });
        
        // Modal close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }
    
    // Render column structure
    renderColumns() {
        this.projectsContainer.innerHTML = `
            <div class="board-columns">
                ${this.columns.map(column => `
                    <div class="board-column" data-status="${column}">
                        <div class="column-header">
                            <h3 class="column-title">${column}</h3>
                            <span class="column-count" id="count-${column.replace(/\s+/g, '-')}">0</span>
                        </div>
                        <div class="column-content" id="column-${column.replace(/\s+/g, '-')}">
                            <div class="loading-spinner">
                                <i class="fas fa-spinner fa-spin"></i>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Display projects in columns
    displayProjects(projects) {
        this.projects = projects;
        this.filterProjects();
        this.updateStats();
    }
    
    // Filter projects
    filterProjects() {
        const searchTerm = this.searchInput.value.toLowerCase();
        
        this.filteredProjects = this.projects.filter(project => {
            if (!searchTerm) return true;
            
            return project.title.toLowerCase().includes(searchTerm) ||
                   (project.body || '').toLowerCase().includes(searchTerm) ||
                   project.keywords.some(k => k.toLowerCase().includes(searchTerm));
        });
        
        this.renderProjects();
    }
    
    // Sort projects
    sortProjects(sortBy) {
        const sortFunctions = {
            'updated': (a, b) => new Date(b.updated_at) - new Date(a.updated_at),
            'created': (a, b) => new Date(b.created_at) - new Date(a.created_at),
            'title': (a, b) => a.title.localeCompare(b.title),
            'votes': (a, b) => (b.votes.up - b.votes.down) - (a.votes.up - a.votes.down),
            'views': (a, b) => b.views - a.views
        };
        
        if (sortFunctions[sortBy]) {
            this.projects.sort(sortFunctions[sortBy]);
            this.filterProjects();
        }
    }
    
    // Render projects in columns
    renderProjects() {
        // Group projects by status
        const grouped = {};
        this.columns.forEach(col => grouped[col] = []);
        
        this.filteredProjects.forEach(project => {
            const status = project.projectStatus || 'Backlog';
            if (grouped[status]) {
                grouped[status].push(project);
            }
        });
        
        // Render each column
        this.columns.forEach(column => {
            const container = document.getElementById(`column-${column.replace(/\s+/g, '-')}`);
            const count = document.getElementById(`count-${column.replace(/\s+/g, '-')}`);
            const projects = grouped[column] || [];
            
            count.textContent = projects.length;
            
            if (projects.length === 0) {
                container.innerHTML = `
                    <div class="empty-column">
                        <i class="fas fa-inbox"></i>
                        <p>No projects</p>
                    </div>
                `;
            } else {
                container.innerHTML = projects.map(project => this.renderProjectCard(project)).join('');
            }
        });
    }
    
    // Render individual project card
    renderProjectCard(project) {
        const userReacted = project.userReactions || { up: false, down: false };
        
        return `
            <div class="project-card" onclick="ui.showProject(${project.number})">
                <h4 class="project-title">${this.escapeHtml(project.title)}</h4>
                
                <div class="project-meta">
                    <span class="meta-item">
                        <img src="${project.user.avatar_url}" alt="${project.user.login}" class="meta-avatar">
                        ${project.user.login}
                    </span>
                    <span class="meta-item">
                        <i class="fas fa-calendar"></i>
                        ${this.formatDate(project.created_at)}
                    </span>
                </div>
                
                <p class="project-description">
                    ${this.truncateText(this.escapeHtml(project.body || ''), 150)}
                </p>
                
                <div class="project-actions">
                    <button class="vote-btn ${userReacted.up ? 'active' : ''}" 
                            onclick="event.stopPropagation(); ui.vote(${project.number}, '+1')">
                        <i class="fas fa-thumbs-up"></i> ${project.votes.up}
                    </button>
                    <button class="vote-btn ${userReacted.down ? 'active' : ''}" 
                            onclick="event.stopPropagation(); ui.vote(${project.number}, '-1')">
                        <i class="fas fa-thumbs-down"></i> ${project.votes.down}
                    </button>
                    <span class="meta-item">
                        <i class="fas fa-eye"></i> ${project.views}
                    </span>
                </div>
                
                ${project.keywords.length > 0 ? `
                    <div class="project-keywords">
                        ${project.keywords.slice(0, 3).map(k => 
                            `<span class="keyword-tag">${this.escapeHtml(k)}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // Show project details
    async showProject(issueNumber) {
        const project = this.projects.find(p => p.number === issueNumber);
        if (!project) return;
        
        // Track view
        window.api.trackView(issueNumber);
        project.views = window.api.getViews(issueNumber);
        
        const modalContent = document.getElementById('modalContent');
        modalContent.innerHTML = `
            <div class="modal-header">
                <h2>${this.escapeHtml(project.title)}</h2>
                <div class="modal-meta">
                    <span class="project-status status-${project.projectStatus.toLowerCase().replace(/\s+/g, '-')}">
                        ${project.projectStatus}
                    </span>
                    <a href="${project.html_url}" target="_blank" class="btn-text">
                        <i class="fab fa-github"></i> View on GitHub
                    </a>
                </div>
            </div>
            
            <div class="modal-body">
                <div class="issue-meta">
                    <img src="${project.user.avatar_url}" alt="${project.user.login}" class="issue-avatar">
                    <div>
                        <strong>${project.user.login}</strong>
                        <br>
                        <small>${this.formatDate(project.created_at)}</small>
                    </div>
                </div>
                
                <div class="issue-content">
                    ${this.renderMarkdown(project.body || '')}
                </div>
                
                ${project.keywords.length > 0 ? `
                    <div class="issue-keywords">
                        ${project.keywords.map(k => 
                            `<span class="keyword-tag">${this.escapeHtml(k)}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
            
            <div class="modal-footer">
                <div class="vote-section">
                    <button class="vote-btn large ${project.userReactions?.up ? 'active' : ''}" 
                            onclick="ui.vote(${project.number}, '+1')">
                        <i class="fas fa-thumbs-up"></i> ${project.votes.up}
                    </button>
                    <button class="vote-btn large ${project.userReactions?.down ? 'active' : ''}" 
                            onclick="ui.vote(${project.number}, '-1')">
                        <i class="fas fa-thumbs-down"></i> ${project.votes.down}
                    </button>
                </div>
                <div class="view-count">
                    <i class="fas fa-eye"></i> ${project.views} views
                </div>
            </div>
        `;
        
        document.getElementById('projectModal').classList.add('active');
    }
    
    // Vote on project
    async vote(issueNumber, reaction) {
        // Direct users to GitHub for voting
        window.githubAuth.voteOnIssue(issueNumber, reaction);
    }
    
    // Show submit modal
    showSubmitModal() {
        document.getElementById('submitModal').classList.add('active');
        setTimeout(() => {
            document.getElementById('ideaTitle').focus();
        }, 100);
    }
    
    // Handle form submission
    async handleSubmit(e) {
        e.preventDefault();
        
        const title = document.getElementById('ideaTitle').value.trim();
        const description = document.getElementById('ideaDescription').value.trim();
        const keywords = document.getElementById('ideaKeywords').value
            .split(',')
            .map(k => k.trim())
            .filter(k => k);
        
        if (!title || !description) {
            this.showToast('Please fill in all required fields', 'error');
            return;
        }
        
        // Direct to GitHub for issue creation
        window.githubAuth.createIssue(title, description, keywords);
        
        // Close modal and reset form
        this.submitForm.reset();
        document.getElementById('submitModal').classList.remove('active');
    }
    
    // Update statistics
    updateStats() {
        document.getElementById('totalProjects').textContent = this.projects.length;
        
        const totalViews = this.projects.reduce((sum, p) => sum + p.views, 0);
        document.getElementById('totalViews').textContent = this.formatNumber(totalViews);
        
        const totalVotes = this.projects.reduce((sum, p) => sum + p.votes.up + p.votes.down, 0);
        document.getElementById('totalVotes').textContent = this.formatNumber(totalVotes);
    }
    
    // Load projects with auth check
    async loadProjects() {
        try {
            const projects = await window.api.fetchProjectIssues();
            
            // If authenticated, get user reactions
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                for (const project of projects) {
                    const reactions = await window.api.getUserReactions(project.number);
                    project.userReactions = {
                        up: reactions.some(r => r.content === '+1'),
                        down: reactions.some(r => r.content === '-1')
                    };
                }
            }
            
            this.displayProjects(projects);
            
        } catch (error) {
            console.error('Error loading projects:', error);
            this.showToast('Failed to load projects', 'error');
        }
    }
    
    // Utility functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const days = Math.floor(diff / 86400000);
        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
        
        return date.toLocaleDateString();
    }
    
    formatNumber(num) {
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
    
    renderMarkdown(text) {
        // Basic markdown rendering
        return text
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation' : type === 'success' ? 'check' : 'info'}-circle"></i> ${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
}

// Modal functions
function closeModal() {
    document.getElementById('projectModal').classList.remove('active');
}

function closeSubmitModal() {
    document.getElementById('submitModal').classList.remove('active');
}

// Initialize UI
window.ui = new BoardUI();