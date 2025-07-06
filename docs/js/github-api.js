// GitHub API with full authentication support
class GitHubAPI {
    constructor() {
        this.baseUrl = 'https://api.github.com';
        this.owner = CONFIG.github.owner;
        this.repo = CONFIG.github.repo;
    }
    
    // Get auth headers
    getHeaders() {
        const headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        };
        
        if (window.githubAuth && window.githubAuth.isAuthenticated()) {
            Object.assign(headers, window.githubAuth.getAuthHeaders());
        }
        
        return headers;
    }
    
    // Fetch all issues with full details
    async fetchProjectIssues() {
        try {
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues?state=open&per_page=100`,
                { headers: this.getHeaders() }
            );
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            const issues = await response.json();
            
            // Filter out pull requests and enrich data
            const enrichedIssues = await Promise.all(issues
                .filter(issue => !issue.pull_request)
                .map(async issue => {
                    const realAuthor = await this.getRealAuthor(issue);
                    // Clean up title by removing "Title: " prefix
                    const cleanTitle = issue.title.replace(/^Title:\s*/i, '');
                    return {
                        ...issue,
                        title: cleanTitle,
                        projectStatus: this.getStatusFromLabels(issue.labels),
                        keywords: this.extractKeywords(issue),
                        views: this.getViews(issue.number),
                        votes: {
                            up: issue.reactions['+1'] || 0,
                            down: issue.reactions['-1'] || 0
                        },
                        realAuthor: realAuthor
                    };
                }));
            
            return enrichedIssues;
            
        } catch (error) {
            console.error('Error fetching issues:', error);
            throw error;
        }
    }
    
    // Get real author from comments attribution
    async getRealAuthor(issue) {
        try {
            // If the issue author is github-actions[bot] or similar automation, look for attribution in comments
            if (this.isAutomationBot(issue.user.login)) {
                const comments = await window.githubAuth.getComments(issue.number);
                
                // Look for attribution patterns in comments
                for (const comment of comments) {
                    const attribution = this.extractAttribution(comment.body);
                    if (attribution) {
                        return {
                            name: attribution,
                            type: this.isHumanAuthor(attribution) ? 'human' : 'ai',
                            source: 'attribution'
                        };
                    }
                }
                
                // Look for attribution in issue body
                const bodyAttribution = this.extractAttribution(issue.body);
                if (bodyAttribution) {
                    return {
                        name: bodyAttribution,
                        type: this.isHumanAuthor(bodyAttribution) ? 'human' : 'ai',
                        source: 'body'
                    };
                }
                
                // Default to automation system
                return {
                    name: 'llm-automation',
                    type: 'ai',
                    source: 'default'
                };
            }
            
            // For human authors, check if they're actually LLM-generated content
            if (issue.user.login === 'jeremymanning') {
                const comments = await window.githubAuth.getComments(issue.number);
                
                // Look for LLM attribution in comments or body
                for (const comment of comments) {
                    const attribution = this.extractAttribution(comment.body);
                    if (attribution && !this.isHumanAuthor(attribution)) {
                        return {
                            name: attribution,
                            type: 'ai',
                            source: 'override'
                        };
                    }
                }
                
                const bodyAttribution = this.extractAttribution(issue.body);
                if (bodyAttribution && !this.isHumanAuthor(bodyAttribution)) {
                    return {
                        name: bodyAttribution,
                        type: 'ai',
                        source: 'override'
                    };
                }
            }
            
            // Default to the GitHub user
            return {
                name: issue.user.login,
                type: this.isHumanAuthor(issue.user.login) ? 'human' : 'ai',
                source: 'github'
            };
            
        } catch (error) {
            console.error('Error getting real author:', error);
            return {
                name: issue.user.login,
                type: 'unknown',
                source: 'error'
            };
        }
    }
    
    // Check if user is an automation bot
    isAutomationBot(username) {
        const automationIndicators = [
            'github-actions[bot]',
            'github-actions',
            'dependabot[bot]',
            'dependabot'
        ];
        return automationIndicators.some(indicator => username.toLowerCase().includes(indicator.toLowerCase()));
    }
    
    // Extract attribution from text
    extractAttribution(text) {
        if (!text) return null;
        
        // Look for various attribution patterns
        const patterns = [
            /(?:Author|Reviewer|Generated by):\s*([^\n\r,]+)/i,
            /\*\*(?:Author|Reviewer|Generated by)\*\*:\s*([^\n\r,]+)/i,
            /(?:by|from)\s+(claude|gpt|qwen|llama|tinyllama|hermes|phi|mistral|openai|anthropic)[\s-]?[^\s\n\r,]*/i,
            /(?:model|llm):\s*([^\n\r,]+)/i,
            /Generated with.*?\[(.*?)\]/i
        ];
        
        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match && match[1]) {
                // Clean up the extracted name by removing markdown formatting
                return match[1].trim().replace(/\*\*/g, '').replace(/\*/g, '');
            }
        }
        
        return null;
    }
    
    // Check if author name indicates human vs AI
    isHumanAuthor(name) {
        if (!name) return false;
        
        const aiIndicators = [
            'claude', 'gpt', 'openai', 'anthropic', 'llm', 'automation',
            'qwen', 'llama', 'mistral', 'tinyllama', 'hermes', 'phi',
            'chatgpt', 'copilot', 'assistant'
        ];
        
        const nameLower = name.toLowerCase();
        return !aiIndicators.some(indicator => nameLower.includes(indicator));
    }
    
    // Create a new issue
    async createIssue(title, body, labels = []) {
        if (!window.githubAuth || !window.githubAuth.isAuthenticated()) {
            throw new Error('Authentication required');
        }
        
        try {
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues`,
                {
                    method: 'POST',
                    headers: this.getHeaders(),
                    body: JSON.stringify({
                        title,
                        body,
                        labels
                    })
                }
            );
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to create issue');
            }
            
            const issue = await response.json();
            return issue;
            
        } catch (error) {
            console.error('Error creating issue:', error);
            throw error;
        }
    }
    
    // Add reaction to issue
    async addReaction(issueNumber, reaction) {
        if (!window.githubAuth || !window.githubAuth.isAuthenticated()) {
            throw new Error('Authentication required');
        }
        
        try {
            // First, check if user already reacted
            const existingReactions = await this.getUserReactions(issueNumber);
            const existingReaction = existingReactions.find(r => r.content === reaction);
            
            if (existingReaction) {
                // Remove existing reaction
                await this.removeReaction(issueNumber, existingReaction.id);
            } else {
                // Add new reaction
                const response = await fetch(
                    `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues/${issueNumber}/reactions`,
                    {
                        method: 'POST',
                        headers: {
                            ...this.getHeaders(),
                            'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                        },
                        body: JSON.stringify({ content: reaction })
                    }
                );
                
                if (!response.ok) {
                    throw new Error('Failed to add reaction');
                }
            }
            
            return true;
            
        } catch (error) {
            console.error('Error adding reaction:', error);
            throw error;
        }
    }
    
    // Get user's reactions on an issue
    async getUserReactions(issueNumber) {
        if (!window.githubAuth || !window.githubAuth.isAuthenticated()) {
            return [];
        }
        
        const user = window.githubAuth.getUser();
        
        try {
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues/${issueNumber}/reactions`,
                {
                    headers: {
                        ...this.getHeaders(),
                        'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                    }
                }
            );
            
            if (!response.ok) return [];
            
            const reactions = await response.json();
            return reactions.filter(r => r.user.login === user.login);
            
        } catch (error) {
            console.error('Error fetching reactions:', error);
            return [];
        }
    }
    
    // Remove reaction
    async removeReaction(issueNumber, reactionId) {
        try {
            await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues/${issueNumber}/reactions/${reactionId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...this.getHeaders(),
                        'Accept': 'application/vnd.github.squirrel-girl-preview+json'
                    }
                }
            );
        } catch (error) {
            console.error('Error removing reaction:', error);
        }
    }
    
    // Get status from labels
    getStatusFromLabels(labels) {
        const statusMap = {
            'backlog': 'Backlog',
            'ready': 'Ready',
            'in progress': 'In Progress',
            'in-progress': 'In Progress',
            'in review': 'In Review',
            'in-review': 'In Review',
            'done': 'Done',
            'completed': 'Done'
        };
        
        // Debug logging
        if (labels.length > 0) {
            console.log('Checking labels for status:', labels.map(l => l.name));
        }
        
        // Check for exact matches first (case-insensitive)
        for (const label of labels) {
            const labelName = label.name.toLowerCase().trim();
            if (statusMap[labelName]) {
                console.log(`Found exact status match: "${label.name}" -> "${statusMap[labelName]}"`);
                return statusMap[labelName];
            }
        }
        
        // Then check for partial matches
        for (const label of labels) {
            const labelName = label.name.toLowerCase().trim();
            for (const [key, status] of Object.entries(statusMap)) {
                if (labelName.includes(key)) {
                    console.log(`Found partial status match: "${label.name}" contains "${key}" -> "${status}"`);
                    return status;
                }
            }
        }
        
        console.log('No status label found, defaulting to Backlog');
        return 'Backlog'; // Default
    }
    
    // Extract keywords
    extractKeywords(issue) {
        const keywords = [];
        
        // Get from labels (exclude status labels)
        issue.labels.forEach(label => {
            const name = label.name.toLowerCase();
            // More comprehensive status label exclusion
            if (!['backlog', 'ready', 'in progress', 'in-progress', 'in review', 'in-review', 'done', 'completed'].some(s => name === s || name.includes(s))) {
                keywords.push(label.name);
            }
        });
        
        return keywords;
    }
    
    // View tracking
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
}

// Initialize API
window.api = new GitHubAPI();