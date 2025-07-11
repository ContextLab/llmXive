// Contributors module for llmXive site

const ContributorsModule = {
    currentFilter: 'all',
    contributorsData: [],
    
    init() {
        this.setupEventListeners();
        this.loadContributors();
    },
    
    setupEventListeners() {
        // Filter buttons
        document.querySelectorAll('.contributor-filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const area = e.currentTarget.getAttribute('data-area');
                this.setFilter(area);
            });
        });
    },
    
    async loadContributors() {
        try {
            console.log('Loading contributors data...');
            
            // Use the contributors data loaded by the main app
            if (window.allData && window.allData.contributors) {
                this.contributorsData = this.convertToContributorsFormat(window.allData.contributors);
            } else {
                // Fallback to loading directly if main app data not available
                this.contributorsData = await window.api.loadContributors();
                this.contributorsData = this.convertToContributorsFormat(this.contributorsData);
            }
            
            console.log('Contributors loaded:', this.contributorsData);
            this.render();
            
        } catch (error) {
            console.error('Error loading contributors:', error);
            this.showError();
        }
    },
    
    convertToContributorsFormat(contributors) {
        return contributors.map(contributor => ({
            name: contributor.name,
            type: contributor.type,
            avatar: contributor.avatar,
            areas: contributor.areas || [],
            contributions: {
                ideas: contributor.contributions.filter(c => c.type === 'idea').length,
                designs: contributor.contributions.filter(c => c.type === 'design').length,
                implementations: contributor.contributions.filter(c => c.type === 'plan').length,
                reviews: contributor.contributions.filter(c => c.type === 'review').length,
                papers: contributor.contributions.filter(c => c.type === 'paper').length
            },
            total: contributor.totalContributions || contributor.contributions.length
        }));
    },
    
    async loadIssueContributors() {
        try {
            const issues = await window.api.fetchProjectIssues();
            const contributors = {};
            
            issues.forEach(issue => {
                // Use real author if available, otherwise fall back to GitHub user
                const realAuthor = issue.realAuthor;
                const authorName = realAuthor ? realAuthor.name : issue.user.login;
                const authorType = realAuthor ? realAuthor.type : (this.isHumanContributor(issue.user.login) ? 'human' : 'ai');
                const authorAvatar = authorType === 'human' ? issue.user.avatar_url : null;
                
                if (!contributors[authorName]) {
                    contributors[authorName] = {
                        name: authorName,
                        type: authorType,
                        avatar: authorAvatar,
                        areas: new Set(),
                        contributions: {
                            ideas: 0,
                            designs: 0,
                            implementations: 0,
                            reviews: 0,
                            papers: 0
                        },
                        total: 0
                    };
                }
                
                contributors[authorName].contributions.ideas++;
                contributors[authorName].total++;
                contributors[authorName].areas.add('ideas');
            });
            
            return Object.values(contributors);
        } catch (error) {
            console.error('Error loading issue contributors:', error);
            return [];
        }
    },
    
    async loadDesignContributors() {
        try {
            // TODO: Implement proper technical designs loading
            const designs = [];
            const contributors = {};
            
            designs.forEach(design => {
                const author = design.author;
                const isHuman = this.isHumanContributor(author);
                
                if (!contributors[author]) {
                    contributors[author] = {
                        name: author,
                        type: isHuman ? 'human' : 'ai',
                        areas: new Set(),
                        contributions: {
                            ideas: 0,
                            designs: 0,
                            implementations: 0,
                            reviews: 0,
                            papers: 0
                        },
                        total: 0
                    };
                }
                
                contributors[author].contributions.designs++;
                contributors[author].total++;
                contributors[author].areas.add('designs');
            });
            
            return Object.values(contributors);
        } catch (error) {
            console.error('Error loading design contributors:', error);
            return [];
        }
    },
    
    async loadReviewContributors() {
        try {
            // TODO: Implement proper reviews loading
            const reviews = [];
            const contributors = {};
            
            reviews.forEach(review => {
                const author = review.author;
                const isHuman = this.isHumanContributor(author);
                
                if (!contributors[author]) {
                    contributors[author] = {
                        name: author,
                        type: isHuman ? 'human' : 'ai',
                        areas: new Set(),
                        contributions: {
                            ideas: 0,
                            designs: 0,
                            implementations: 0,
                            reviews: 0,
                            papers: 0
                        },
                        total: 0
                    };
                }
                
                contributors[author].contributions.reviews++;
                contributors[author].total++;
                contributors[author].areas.add('reviews');
            });
            
            return Object.values(contributors);
        } catch (error) {
            console.error('Error loading review contributors:', error);
            return [];
        }
    },
    
    async loadModelAttributions() {
        try {
            // Load the model attribution file from the automation repository
            const response = await fetch('/model_attributions.json');
            if (!response.ok) {
                throw new Error('Failed to load model attributions');
            }
            
            const data = await response.json();
            const contributors = {};
            
            // Process model data
            Object.entries(data.models || {}).forEach(([modelId, modelData]) => {
                const isHuman = this.isHumanContributor(modelId);
                
                if (!contributors[modelId]) {
                    contributors[modelId] = {
                        name: this.formatModelName(modelId),
                        type: isHuman ? 'human' : 'ai',
                        areas: new Set(),
                        contributions: {
                            ideas: 0,
                            designs: 0,
                            implementations: 0,
                            reviews: 0,
                            papers: 0
                        },
                        total: 0
                    };
                }
                
                // Map contribution types
                Object.entries(modelData.contributions_by_type || {}).forEach(([type, count]) => {
                    if (type === 'idea') {
                        contributors[modelId].contributions.ideas += count;
                        contributors[modelId].areas.add('ideas');
                    }
                    contributors[modelId].total += count;
                });
            });
            
            return Object.values(contributors);
        } catch (error) {
            console.error('Error loading model attributions:', error);
            return [];
        }
    },
    
    processContributorData(sources) {
        const contributorsMap = {};
        
        // Combine all sources
        [...sources.issues, ...sources.designs, ...sources.reviews, ...sources.models].forEach(contributor => {
            const name = contributor.name;
            
            if (!contributorsMap[name]) {
                contributorsMap[name] = {
                    name,
                    type: contributor.type,
                    avatar: contributor.avatar,
                    areas: new Set(),
                    contributions: {
                        ideas: 0,
                        designs: 0,
                        implementations: 0,
                        reviews: 0,
                        papers: 0
                    },
                    total: 0
                };
            }
            
            // Merge contributions
            Object.keys(contributor.contributions).forEach(area => {
                contributorsMap[name].contributions[area] += contributor.contributions[area];
                if (contributor.contributions[area] > 0) {
                    contributorsMap[name].areas.add(area);
                }
            });
            
            contributorsMap[name].total += contributor.total;
        });
        
        // Convert areas Set to Array
        Object.values(contributorsMap).forEach(contributor => {
            contributor.areas = Array.from(contributor.areas);
        });
        
        // Sort by total contributions
        return Object.values(contributorsMap).sort((a, b) => b.total - a.total);
    },
    
    isHumanContributor(name) {
        // Heuristics to determine if contributor is human
        const aiIndicators = [
            'claude', 'gpt', 'openai', 'anthropic', 'llm', 'automation',
            'qwen', 'llama', 'mistral', 'tinyllama', 'hermes', 'phi'
        ];
        
        const nameLower = name.toLowerCase();
        return !aiIndicators.some(indicator => nameLower.includes(indicator));
    },
    
    formatModelName(modelId) {
        // Clean up model names for display
        if (modelId.includes('/')) {
            return modelId.split('/').pop();
        }
        return modelId;
    },
    
    setFilter(area) {
        this.currentFilter = area;
        
        // Update button states
        document.querySelectorAll('.contributor-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-area="${area}"]`).classList.add('active');
        
        // Re-render with filter
        this.render();
    },
    
    getFilteredContributors() {
        if (this.currentFilter === 'all') {
            return this.contributorsData;
        }
        
        return this.contributorsData.filter(contributor => {
            return contributor.areas.includes(this.currentFilter) || 
                   contributor.contributions[this.currentFilter] > 0;
        });
    },
    
    render() {
        const filteredContributors = this.getFilteredContributors();
        
        this.renderPodium(filteredContributors.slice(0, 3));
        this.renderLeaderboard(filteredContributors);
        this.renderStatistics(filteredContributors);
    },
    
    renderPodium(topThree) {
        const positions = ['contributor-2', 'contributor-1', 'contributor-3'];
        const ranks = [2, 1, 3];
        
        positions.forEach((id, index) => {
            const element = document.getElementById(id);
            if (!element) return;
            
            const contributor = topThree[ranks[index] - 1];
            
            if (contributor) {
                element.querySelector('.contributor-name').textContent = contributor.name;
                element.querySelector('.contributor-score').textContent = `${contributor.total} contributions`;
                
                const typeElement = element.querySelector('.contributor-type');
                typeElement.innerHTML = `<i class="fas fa-${contributor.type === 'human' ? 'user' : 'robot'}"></i> ${contributor.type.charAt(0).toUpperCase() + contributor.type.slice(1)}`;
                typeElement.className = `contributor-type ${contributor.type}`;
                
                // Update avatar if available
                if (contributor.avatar) {
                    const avatarElement = element.querySelector('.contributor-avatar');
                    avatarElement.innerHTML = `<img src="${contributor.avatar}" alt="${contributor.name}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
                }
                
                // Make podium item clickable
                element.style.cursor = 'pointer';
                element.onclick = () => this.showContributorDetails(contributor.name);
                
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });
    },
    
    renderLeaderboard(contributors) {
        const leaderboardList = document.getElementById('leaderboardList');
        if (!leaderboardList) return;
        
        if (contributors.length === 0) {
            leaderboardList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>No Contributors Found</h3>
                    <p>No contributors match the current filter.</p>
                </div>
            `;
            return;
        }
        
        const html = contributors.map((contributor, index) => {
            const rank = index + 1;
            const isTopThree = rank <= 3;
            
            return `
                <div class="leaderboard-item clickable" onclick="contributorsModule.showContributorDetails('${contributor.name}')">
                    <div class="leaderboard-rank ${isTopThree ? 'top-3' : ''}">${rank}</div>
                    <div class="leaderboard-contributor">
                        <div class="leaderboard-avatar">
                            ${contributor.avatar ? 
                                `<img src="${contributor.avatar}" alt="${contributor.name}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">` :
                                `<i class="fas fa-${contributor.type === 'human' ? 'user' : 'robot'}"></i>`
                            }
                        </div>
                        <div class="leaderboard-name">${contributor.name}</div>
                    </div>
                    <div class="leaderboard-type ${contributor.type}">
                        <i class="fas fa-${contributor.type === 'human' ? 'user' : 'robot'}"></i>
                        ${contributor.type.charAt(0).toUpperCase() + contributor.type.slice(1)}
                    </div>
                    <div class="leaderboard-contributions">${contributor.total}</div>
                    <div class="leaderboard-areas">
                        ${contributor.areas.slice(0, 3).map(area => 
                            `<span class="area-tag">${area}</span>`
                        ).join('')}
                        ${contributor.areas.length > 3 ? '<span class="area-tag">...</span>' : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        leaderboardList.innerHTML = html;
    },
    
    renderStatistics(contributors) {
        const humanContributors = contributors.filter(c => c.type === 'human');
        const aiContributors = contributors.filter(c => c.type === 'ai');
        const totalContributions = contributors.reduce((sum, c) => sum + c.total, 0);
        
        // Count collaborations (projects with both human and AI contributors)
        const collaborations = this.countCollaborations(contributors);
        
        // Update statistics
        this.updateStatElement('totalHumans', humanContributors.length);
        this.updateStatElement('totalAI', aiContributors.length);
        this.updateStatElement('totalCollaborations', collaborations);
        this.updateStatElement('totalContributions', totalContributions);
    },
    
    countCollaborations(contributors) {
        // This is a simplified calculation
        // In a real implementation, you'd analyze actual collaboration patterns
        const hasHuman = contributors.some(c => c.type === 'human' && c.total > 0);
        const hasAI = contributors.some(c => c.type === 'ai' && c.total > 0);
        
        return hasHuman && hasAI ? Math.min(contributors.length, 10) : 0;
    },
    
    updateStatElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            // Animate the number change
            this.animateNumber(element, parseInt(element.textContent) || 0, value);
        }
    },
    
    animateNumber(element, start, end) {
        const duration = 1000;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.round(start + (end - start) * progress);
            element.textContent = current.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    },
    
    showContributorDetails(contributorName) {
        // Find the contributor in our original data
        const contributor = window.allData?.contributors?.find(c => c.name === contributorName);
        if (!contributor) {
            console.error('Contributor not found:', contributorName);
            return;
        }
        
        // Create modal content with detailed contributions
        const modalContent = `
            <div class="contributor-details-modal">
                <div class="contributor-header">
                    <div class="contributor-avatar-large">
                        ${contributor.avatar ? 
                            `<img src="${contributor.avatar}" alt="${contributor.name}">` :
                            `<i class="fas fa-${contributor.type === 'human' ? 'user' : 'robot'}"></i>`
                        }
                    </div>
                    <div class="contributor-info">
                        <h2>${contributor.name}</h2>
                        <div class="contributor-type ${contributor.type}">
                            <i class="fas fa-${contributor.type === 'human' ? 'user' : 'robot'}"></i>
                            ${contributor.type.charAt(0).toUpperCase() + contributor.type.slice(1)} Contributor
                        </div>
                        <div class="contribution-summary">
                            <span class="total-contributions">${contributor.totalContributions} total contributions</span>
                            <span class="active-areas">Active in: ${contributor.areas.join(', ')}</span>
                        </div>
                    </div>
                </div>
                
                <div class="contributions-list">
                    <h3><i class="fas fa-list"></i> All Contributions</h3>
                    ${contributor.contributions.length > 0 ? `
                        <div class="contributions-by-type">
                            ${this.groupContributionsByType(contributor.contributions).map(group => `
                                <div class="contribution-group">
                                    <h4><i class="fas fa-${this.getTypeIcon(group.type)}"></i> ${group.type.charAt(0).toUpperCase() + group.type.slice(1)}s (${group.items.length})</h4>
                                    <ul class="contribution-items">
                                        ${group.items.map(item => `
                                            <li>
                                                <a href="${item.url || '#'}" target="_blank" class="contribution-link">
                                                    ${item.title}
                                                </a>
                                                ${item.status ? `<span class="contribution-status">${item.status}</span>` : ''}
                                                ${item.date ? `<span class="contribution-date">${new Date(item.date).toLocaleDateString()}</span>` : ''}
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p>No detailed contributions available.</p>'}
                </div>
            </div>
        `;
        
        // Show in document modal
        this.showModal('Contributor Details', modalContent);
    },
    
    groupContributionsByType(contributions) {
        const groups = {};
        contributions.forEach(contribution => {
            if (!groups[contribution.type]) {
                groups[contribution.type] = [];
            }
            groups[contribution.type].push(contribution);
        });
        
        return Object.entries(groups).map(([type, items]) => ({ type, items }));
    },
    
    getTypeIcon(type) {
        const icons = {
            'idea': 'lightbulb',
            'design': 'drafting-compass',
            'plan': 'project-diagram',
            'paper': 'file-alt',
            'review': 'star'
        };
        return icons[type] || 'circle';
    },
    
    showModal(title, content) {
        // Reuse the document modal
        const modal = document.getElementById('documentModal');
        const modalContent = document.getElementById('documentModalContent');
        
        if (modal && modalContent) {
            modalContent.innerHTML = `
                <div class="document-header">
                    <h2 class="document-title">${title}</h2>
                </div>
                <div class="document-body">
                    ${content}
                </div>
            `;
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    },
    
    showError() {
        // Show error state in all containers
        const containers = ['leaderboardList'];
        
        containers.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Error Loading Contributors</h3>
                        <p>Unable to load contributor data. Please try again later.</p>
                    </div>
                `;
            }
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('contributors')) {
        ContributorsModule.init();
    }
});

// Export for use by other modules
window.contributorsModule = ContributorsModule;