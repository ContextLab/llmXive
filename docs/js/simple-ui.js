// Simplified UI - Leverages GitHub's native features
class SimpleUI {
    constructor() {
        this.projectsGrid = document.getElementById('projectsGrid');
        this.papersGrid = document.getElementById('papersGrid');
        this.searchInput = document.getElementById('searchInput');
        this.statusFilter = document.getElementById('statusFilter');
        this.sortSelect = document.getElementById('sortSelect');
        this.submitForm = document.getElementById('submitForm');
        
        this.projects = [];
        this.filteredProjects = [];
        this.searchDebounce = null;
        
        this.initializeEventListeners();
    }
    
    // Initialize event listeners
    initializeEventListeners() {
        // Search
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounce);
            this.searchDebounce = setTimeout(() => {
                this.filterProjects();
            }, 300);
        });
        
        // Filters
        this.statusFilter.addEventListener('change', () => this.filterProjects());
        this.sortSelect.addEventListener('change', () => this.sortProjects());
        
        // Submit form
        this.submitForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Submit button
        document.querySelector('a[href="#submit"]').addEventListener('click', (e) => {
            e.preventDefault();
            this.showSubmitModal();
        });
        
        // Modal close on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }
    
    // Display projects
    displayProjects(projects) {
        this.projects = projects;
        this.filteredProjects = projects;
        this.filterProjects();
        this.updateStats();
    }
    
    // Filter projects
    filterProjects() {
        const searchTerm = this.searchInput.value.toLowerCase();
        const statusFilter = this.statusFilter.value;
        
        this.filteredProjects = this.projects.filter(project => {
            const matchesSearch = !searchTerm || 
                project.title.toLowerCase().includes(searchTerm) ||
                (project.body || '').toLowerCase().includes(searchTerm) ||
                project.keywords.some(k => k.toLowerCase().includes(searchTerm));
            
            const matchesStatus = !statusFilter || project.projectStatus === statusFilter;
            
            return matchesSearch && matchesStatus;
        });
        
        this.sortProjects();
    }
    
    // Sort projects
    sortProjects() {
        const sortBy = this.sortSelect.value;
        
        this.filteredProjects.sort((a, b) => {
            switch (sortBy) {
                case 'updated':
                    return new Date(b.updated_at) - new Date(a.updated_at);
                case 'created':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'title':
                    return a.title.localeCompare(b.title);
                case 'votes':
                    return (b.votes.up - b.votes.down) - (a.votes.up - a.votes.down);
                case 'views':
                    return b.views - a.views;
                default:
                    return 0;
            }
        });
        
        this.renderProjects();
    }
    
    // Render projects grid
    renderProjects() {
        if (this.filteredProjects.length === 0) {
            this.projectsGrid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No projects found</p>
                </div>
            `;
            return;
        }
        
        this.projectsGrid.innerHTML = this.filteredProjects.map(project => `
            <div class="project-card" onclick="ui.showProject(${project.number})">
                <div class="project-header">
                    <h3 class="project-title">${this.escapeHtml(project.title)}</h3>
                    <span class="project-status status-${project.projectStatus.toLowerCase().replace(' ', '-')}">
                        ${project.projectStatus}
                    </span>
                </div>
                
                <p class="project-description">
                    ${this.truncateText(this.escapeHtml(project.body || ''), 200)}
                </p>
                
                <div class="project-meta">
                    <span class="meta-item">
                        <i class="fas fa-eye"></i> ${project.views}
                    </span>
                    <span class="meta-item">
                        <i class="fas fa-thumbs-up"></i> ${project.votes.up}
                    </span>
                    <span class="meta-item">
                        <i class="fas fa-thumbs-down"></i> ${project.votes.down}
                    </span>
                    <span class="meta-item">
                        <i class="fas fa-comment"></i> ${project.comments}
                    </span>
                </div>
                
                ${project.keywords.length > 0 ? `
                    <div class="project-keywords">
                        ${project.keywords.slice(0, 5).map(keyword => 
                            `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    // Show project details
    async showProject(issueNumber) {
        const project = this.projects.find(p => p.number === issueNumber);
        if (!project) return;
        
        // Track view
        window.api.trackView(issueNumber);
        project.views = window.api.getViews(issueNumber);
        
        // Update modal content
        const modalContent = document.getElementById('modalContent');
        modalContent.innerHTML = `
            <div class="modal-project-header">
                <h2 class="modal-project-title">${this.escapeHtml(project.title)}</h2>
                <div class="modal-project-meta">
                    <span class="project-status status-${project.projectStatus.toLowerCase().replace(' ', '-')}">
                        ${project.projectStatus}
                    </span>
                    <span><i class="fas fa-user"></i> ${project.user.login}</span>
                    <span><i class="fas fa-calendar"></i> ${this.formatDate(project.created_at)}</span>
                    <span><i class="fas fa-eye"></i> ${project.views} views</span>
                </div>
            </div>
            
            <div class="modal-project-content">
                ${this.renderMarkdown(project.body || '')}
            </div>
            
            ${project.keywords.length > 0 ? `
                <div class="project-keywords">
                    ${project.keywords.map(keyword => 
                        `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`
                    ).join('')}
                </div>
            ` : ''}
            
            <div class="modal-actions">
                <div class="vote-buttons">
                    <button class="vote-btn upvote" onclick="ui.vote(${issueNumber}, 'up')">
                        <i class="fas fa-thumbs-up"></i>
                        <span>${project.votes.up}</span>
                    </button>
                    <button class="vote-btn downvote" onclick="ui.vote(${issueNumber}, 'down')">
                        <i class="fas fa-thumbs-down"></i>
                        <span>${project.votes.down}</span>
                    </button>
                </div>
                
                <a href="${project.html_url}" target="_blank" class="btn-secondary">
                    <i class="fab fa-github"></i> View on GitHub
                </a>
            </div>
            
            <div class="github-hint">
                <i class="fas fa-info-circle"></i>
                Click the thumbs up/down buttons to vote on GitHub
            </div>
        `;
        
        // Show modal
        document.getElementById('projectModal').classList.add('active');
    }
    
    // Vote on project - redirect to GitHub
    vote(issueNumber, type) {
        // Use the simple auth approach
        window.simpleAuth.voteOnIssue(issueNumber, type);
    }
    
    // Show submit modal
    showSubmitModal() {
        document.getElementById('submitModal').classList.add('active');
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
        
        // Use simple auth to create issue
        window.simpleAuth.createIssue(title, description, keywords);
        
        // Close modal and reset form
        this.submitForm.reset();
        document.getElementById('submitModal').classList.remove('active');
        
        // Show info about refresh
        this.showToast('After creating your issue on GitHub, refresh this page to see it here!', 'info');
    }
    
    // Update statistics
    updateStats() {
        document.getElementById('totalProjects').textContent = this.projects.length;
        
        const totalViews = this.projects.reduce((sum, p) => sum + p.views, 0);
        document.getElementById('totalViews').textContent = this.formatNumber(totalViews);
        
        const totalVotes = this.projects.reduce((sum, p) => sum + p.votes.up + p.votes.down, 0);
        document.getElementById('totalVotes').textContent = this.formatNumber(totalVotes);
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
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 30) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }
    
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
    
    renderMarkdown(text) {
        // Simple markdown rendering
        return text
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    // Toast notifications
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
    
    // Display papers (placeholder)
    displayPapers(papers) {
        // Hide papers section if no papers
        document.getElementById('papers').style.display = 'none';
    }
}

// Close modals
function closeModal() {
    document.getElementById('projectModal').classList.remove('active');
}

function closeSubmitModal() {
    document.getElementById('submitModal').classList.remove('active');
}

// Initialize UI
window.ui = new SimpleUI();