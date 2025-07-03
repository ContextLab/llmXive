// UI Components and Interactions
class UI {
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
            }, CONFIG.ui.debounceDelay);
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
        
        // Update stats
        this.updateStats();
    }
    
    // Filter projects
    filterProjects() {
        const searchTerm = this.searchInput.value.toLowerCase();
        const statusFilter = this.statusFilter.value;
        
        this.filteredProjects = this.projects.filter(project => {
            // Search filter
            const matchesSearch = !searchTerm || 
                project.title.toLowerCase().includes(searchTerm) ||
                project.body.toLowerCase().includes(searchTerm) ||
                project.keywords.some(k => k.toLowerCase().includes(searchTerm));
            
            // Status filter
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
                    ${this.truncateText(this.escapeHtml(project.body), CONFIG.ui.maxDescriptionLength)}
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
                        <i class="fas fa-clock"></i> ${this.formatDate(project.updated_at)}
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
        
        // Fetch full issue details
        const issue = await window.api.fetchIssue(issueNumber);
        
        // Update modal content
        const modalContent = document.getElementById('modalContent');
        modalContent.innerHTML = `
            <div class="modal-project-header">
                <h2 class="modal-project-title">${this.escapeHtml(issue.title)}</h2>
                <div class="modal-project-meta">
                    <span class="project-status status-${project.projectStatus.toLowerCase().replace(' ', '-')}">
                        ${project.projectStatus}
                    </span>
                    <span><i class="fas fa-user"></i> ${issue.user.login}</span>
                    <span><i class="fas fa-calendar"></i> ${this.formatDate(issue.created_at)}</span>
                    <span><i class="fas fa-eye"></i> ${project.views} views</span>
                </div>
            </div>
            
            <div class="modal-project-content">
                ${this.renderMarkdown(issue.body)}
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
                    <button class="vote-btn upvote ${this.hasVoted(issueNumber, 'up') ? 'active' : ''}" 
                            onclick="ui.vote(${issueNumber}, 'up')">
                        <i class="fas fa-thumbs-up"></i>
                        <span>${project.votes.up}</span>
                    </button>
                    <button class="vote-btn downvote ${this.hasVoted(issueNumber, 'down') ? 'active' : ''}"
                            onclick="ui.vote(${issueNumber}, 'down')">
                        <i class="fas fa-thumbs-down"></i>
                        <span>${project.votes.down}</span>
                    </button>
                </div>
                
                <a href="${issue.html_url}" target="_blank" class="btn-secondary">
                    <i class="fab fa-github"></i> View on GitHub
                </a>
            </div>
        `;
        
        // Show modal
        document.getElementById('projectModal').classList.add('active');
    }
    
    // Vote on project
    async vote(issueNumber, type) {
        if (!window.auth || !window.auth.isAuthenticated()) {
            this.showAuthPrompt();
            return;
        }
        
        try {
            // Add reaction
            const reaction = type === 'up' ? 'THUMBS_UP' : 'THUMBS_DOWN';
            await window.api.addReaction(issueNumber, reaction);
            
            // Update UI
            const project = this.projects.find(p => p.number === issueNumber);
            if (project) {
                project.votes = window.api.getVotes(issueNumber);
                this.renderProjects();
                
                // Update modal if open
                if (document.getElementById('projectModal').classList.contains('active')) {
                    this.showProject(issueNumber);
                }
            }
            
            // Save vote state
            this.saveVoteState(issueNumber, type);
            
        } catch (error) {
            console.error('Vote error:', error);
            this.showToast('Failed to register vote', 'error');
        }
    }
    
    // Show submit modal
    showSubmitModal() {
        if (!window.auth || !window.auth.isAuthenticated()) {
            this.showAuthPrompt();
            return;
        }
        
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
        
        try {
            // Show loading state
            const submitBtn = this.submitForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            
            // Create issue
            const issue = await window.api.createIssue(title, description, keywords);
            
            // Success
            this.showToast('Idea submitted successfully!', 'success');
            this.submitForm.reset();
            document.getElementById('submitModal').classList.remove('active');
            
            // Refresh projects
            window.loadProjects();
            
        } catch (error) {
            console.error('Submit error:', error);
            this.showToast(error.message || 'Failed to submit idea', 'error');
        } finally {
            // Reset button
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
    
    // Display papers
    displayPapers(papers) {
        if (papers.length === 0) {
            document.getElementById('papers').style.display = 'none';
            return;
        }
        
        document.getElementById('papers').style.display = 'block';
        this.papersGrid.innerHTML = papers.slice(0, 10).map((paper, index) => `
            <div class="paper-card">
                <div class="paper-rank">${index + 1}</div>
                <h3 class="paper-title">${this.escapeHtml(paper.title)}</h3>
                <p class="paper-authors">${this.escapeHtml(paper.authors.join(', '))}</p>
                
                <div class="paper-links">
                    <a href="${paper.pdfUrl}" target="_blank" class="paper-link">
                        <i class="fas fa-file-pdf"></i> PDF
                    </a>
                    ${paper.codeUrl ? `
                        <a href="${paper.codeUrl}" target="_blank" class="paper-link">
                            <i class="fas fa-code"></i> Code
                        </a>
                    ` : ''}
                    ${paper.dataUrl ? `
                        <a href="${paper.dataUrl}" target="_blank" class="paper-link">
                            <i class="fas fa-database"></i> Data
                        </a>
                    ` : ''}
                </div>
            </div>
        `).join('');
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
        // Simple markdown rendering (in production, use a proper library)
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
    
    // Vote state management
    hasVoted(issueNumber, type) {
        const voteState = JSON.parse(localStorage.getItem('vote_state') || '{}');
        return voteState[issueNumber] === type;
    }
    
    saveVoteState(issueNumber, type) {
        const voteState = JSON.parse(localStorage.getItem('vote_state') || '{}');
        voteState[issueNumber] = type;
        localStorage.setItem('vote_state', JSON.stringify(voteState));
    }
    
    // Auth prompt
    showAuthPrompt() {
        this.showToast('Please login with GitHub to continue', 'info');
        window.auth.login();
    }
    
    // Toast notifications
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
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
window.ui = new UI();