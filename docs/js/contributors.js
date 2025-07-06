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
            
            // Load from multiple sources
            const [issueContributors, designContributors, reviewContributors, modelAttributions] = await Promise.all([
                this.loadIssueContributors(),
                this.loadDesignContributors(),
                this.loadReviewContributors(),
                this.loadModelAttributions()
            ]);
            
            // Combine and process all contributor data
            this.contributorsData = this.processContributorData({
                issues: issueContributors,
                designs: designContributors,
                reviews: reviewContributors,
                models: modelAttributions
            });
            
            console.log('Contributors loaded:', this.contributorsData);
            this.render();
            
        } catch (error) {
            console.error('Error loading contributors:', error);
            this.showError();
        }
    },
    
    async loadIssueContributors() {
        try {
            const issues = await githubAPI.getIssues();
            const contributors = {};
            
            issues.forEach(issue => {
                const username = issue.user.login;
                const isHuman = this.isHumanContributor(username);
                
                if (!contributors[username]) {
                    contributors[username] = {
                        name: username,
                        type: isHuman ? 'human' : 'ai',
                        avatar: issue.user.avatar_url,
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
                
                contributors[username].contributions.ideas++;
                contributors[username].total++;
                contributors[username].areas.add('ideas');
            });
            
            return Object.values(contributors);
        } catch (error) {
            console.error('Error loading issue contributors:', error);
            return [];
        }
    },
    
    async loadDesignContributors() {
        try {
            const designs = await githubAPI.getTechnicalDesigns();
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
            const reviews = await githubAPI.getReviews();
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
                <div class="leaderboard-item">
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