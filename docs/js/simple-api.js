// Simplified GitHub API - Works with public repos, no auth needed!
class SimpleGitHubAPI {
    constructor() {
        this.baseUrl = 'https://api.github.com';
        this.owner = 'ContextLab';
        this.repo = 'llmXive';
        this.projectNumber = 13;
    }
    
    // Fetch all issues with reactions (votes)
    async fetchProjectIssues() {
        try {
            // For public repos, no auth needed!
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues?state=open&per_page=100`,
                {
                    headers: {
                        'Accept': 'application/vnd.github.v3+json'
                    }
                }
            );
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            const issues = await response.json();
            
            // Filter out pull requests and enrich with our data
            const enrichedIssues = issues
                .filter(issue => !issue.pull_request)
                .map(issue => ({
                    ...issue,
                    projectStatus: this.getStatusFromLabels(issue.labels),
                    keywords: this.extractKeywords(issue),
                    views: this.getViews(issue.number),
                    votes: {
                        up: issue.reactions['+1'] || 0,
                        down: issue.reactions['-1'] || 0
                    }
                }));
            
            return enrichedIssues;
            
        } catch (error) {
            console.error('Error fetching issues:', error);
            return [];
        }
    }
    
    // Get status from labels
    getStatusFromLabels(labels) {
        const statusLabels = {
            'backlog': 'Backlog',
            'ready': 'Ready',
            'in-progress': 'In progress',
            'in-review': 'In review',
            'done': 'Done'
        };
        
        for (const label of labels) {
            const labelName = label.name.toLowerCase();
            for (const [key, status] of Object.entries(statusLabels)) {
                if (labelName.includes(key)) {
                    return status;
                }
            }
        }
        
        return 'Backlog'; // Default
    }
    
    // Extract keywords from issue
    extractKeywords(issue) {
        const keywords = [];
        
        // Get keywords from labels
        issue.labels.forEach(label => {
            // Exclude status labels
            if (!['backlog', 'ready', 'in-progress', 'in-review', 'done', 'score'].some(
                status => label.name.toLowerCase().includes(status)
            )) {
                keywords.push(label.name);
            }
        });
        
        // Extract keywords from body
        const bodyMatch = issue.body?.match(/\*\*Keywords\*\*:\s*([^\n]+)/);
        if (bodyMatch) {
            const bodyKeywords = bodyMatch[1].split(',').map(k => k.trim()).filter(k => k && k !== 'none');
            keywords.push(...bodyKeywords);
        }
        
        return [...new Set(keywords)]; // Remove duplicates
    }
    
    // Fetch single issue details
    async fetchIssue(issueNumber) {
        const response = await fetch(
            `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues/${issueNumber}`,
            {
                headers: {
                    'Accept': 'application/vnd.github.v3+json'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`Failed to fetch issue: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // Get reactions for an issue
    async getReactions(issueNumber) {
        const issue = await this.fetchIssue(issueNumber);
        return {
            up: issue.reactions['+1'] || 0,
            down: issue.reactions['-1'] || 0,
            heart: issue.reactions['heart'] || 0,
            rocket: issue.reactions['rocket'] || 0,
            total: issue.reactions.total_count || 0
        };
    }
    
    // View tracking (localStorage only since we can't modify GitHub)
    trackView(issueNumber) {
        const views = JSON.parse(localStorage.getItem('llmxive_views') || '{}');
        views[issueNumber] = (views[issueNumber] || 0) + 1;
        localStorage.setItem('llmxive_views', JSON.stringify(views));
        return views[issueNumber];
    }
    
    getViews(issueNumber) {
        const views = JSON.parse(localStorage.getItem('llmxive_views') || '{}');
        return views[issueNumber] || 0;
    }
    
    // Check if current user has reacted (by username)
    async hasUserReacted(issueNumber, username) {
        if (!username) return { up: false, down: false };
        
        try {
            // Fetch reactions for the issue
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues/${issueNumber}/reactions`,
                {
                    headers: {
                        'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                    }
                }
            );
            
            if (!response.ok) return { up: false, down: false };
            
            const reactions = await response.json();
            
            // Check if user has reacted
            const userReactions = reactions.filter(r => r.user.login === username);
            
            return {
                up: userReactions.some(r => r.content === '+1'),
                down: userReactions.some(r => r.content === '-1')
            };
        } catch (error) {
            console.error('Error checking reactions:', error);
            return { up: false, down: false };
        }
    }
    
    // Fetch completed papers (mock for now)
    async fetchCompletedPapers() {
        // In the future, this could fetch from a specific folder in the repo
        // For now, return empty array
        return [];
    }
    
    // Simple cache implementation
    cache = new Map();
    
    async cachedFetch(key, fetcher, ttl = 300000) { // 5 min TTL
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < ttl) {
            return cached.data;
        }
        
        const data = await fetcher();
        this.cache.set(key, { data, timestamp: Date.now() });
        return data;
    }
    
    // Clear cache
    clearCache() {
        this.cache.clear();
    }
}

// Initialize API
window.api = new SimpleGitHubAPI();