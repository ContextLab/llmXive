// GitHub API Integration
class GitHubAPI {
    constructor() {
        this.baseUrl = CONFIG.api.baseUrl;
        this.graphqlUrl = CONFIG.api.graphqlUrl;
        this.owner = CONFIG.github.owner;
        this.repo = CONFIG.github.repo;
        this.projectNumber = CONFIG.github.projectNumber;
    }
    
    // Get authorization header
    getAuthHeader() {
        // Use OAuth token if authenticated, otherwise no auth for public read
        if (window.auth && window.auth.isAuthenticated()) {
            return { 'Authorization': `Bearer ${window.auth.getToken()}` };
        }
        return {};
    }
    
    // Fetch issues with project board data
    async fetchProjectIssues() {
        const cacheKey = 'project_issues';
        const cached = this.getCache(cacheKey);
        if (cached) return cached;
        
        try {
            // Fetch all open issues
            const issues = await this.fetchAllIssues();
            
            // Fetch project data to get status
            const projectData = await this.fetchProjectData();
            
            // Merge issue data with project status
            const enrichedIssues = issues.map(issue => {
                const projectItem = projectData.items.find(
                    item => item.content?.number === issue.number
                );
                
                return {
                    ...issue,
                    projectStatus: projectItem?.fieldValues?.status || 'Backlog',
                    keywords: this.extractKeywords(issue),
                    views: this.getViews(issue.number),
                    votes: this.getVotes(issue.number)
                };
            });
            
            this.setCache(cacheKey, enrichedIssues);
            return enrichedIssues;
            
        } catch (error) {
            console.error('Error fetching project issues:', error);
            return [];
        }
    }
    
    // Fetch all issues
    async fetchAllIssues() {
        const allIssues = [];
        let page = 1;
        let hasMore = true;
        
        while (hasMore) {
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues?` +
                `state=open&per_page=${CONFIG.api.perPage}&page=${page}`,
                {
                    headers: {
                        'Accept': 'application/vnd.github.v3+json',
                        ...this.getAuthHeader()
                    }
                }
            );
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            const issues = await response.json();
            allIssues.push(...issues.filter(issue => !issue.pull_request));
            
            hasMore = issues.length === CONFIG.api.perPage;
            page++;
        }
        
        return allIssues;
    }
    
    // Fetch project board data using GraphQL
    async fetchProjectData() {
        const query = `
            query($owner: String!, $repo: String!, $number: Int!) {
                repository(owner: $owner, name: $repo) {
                    projectV2(number: $number) {
                        items(first: 100) {
                            nodes {
                                id
                                content {
                                    ... on Issue {
                                        number
                                        title
                                    }
                                }
                                fieldValues(first: 10) {
                                    nodes {
                                        ... on ProjectV2ItemFieldSingleSelectValue {
                                            name
                                            field {
                                                ... on ProjectV2SingleSelectField {
                                                    name
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        `;
        
        const response = await fetch(this.graphqlUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...this.getAuthHeader()
            },
            body: JSON.stringify({
                query,
                variables: {
                    owner: this.owner,
                    repo: this.repo,
                    number: this.projectNumber
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`GraphQL error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Transform the data
        const items = data.data?.repository?.projectV2?.items?.nodes || [];
        return {
            items: items.map(item => ({
                content: item.content,
                fieldValues: {
                    status: item.fieldValues.nodes.find(
                        field => field.field?.name === 'Status'
                    )?.name || 'Backlog'
                }
            }))
        };
    }
    
    // Create a new issue
    async createIssue(title, body, labels = []) {
        if (!window.auth || !window.auth.isAuthenticated()) {
            throw new Error('Authentication required');
        }
        
        const response = await fetch(
            `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.github.v3+json',
                    ...this.getAuthHeader()
                },
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
        
        // Add to project board
        await this.addIssueToProject(issue.node_id);
        
        return issue;
    }
    
    // Add issue to project board
    async addIssueToProject(issueId) {
        const mutation = `
            mutation($projectId: ID!, $contentId: ID!) {
                addProjectV2ItemById(input: {
                    projectId: $projectId,
                    contentId: $contentId
                }) {
                    item {
                        id
                    }
                }
            }
        `;
        
        // First need to get project ID
        const projectId = await this.getProjectId();
        
        const response = await fetch(this.graphqlUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...this.getAuthHeader()
            },
            body: JSON.stringify({
                query: mutation,
                variables: {
                    projectId,
                    contentId: issueId
                }
            })
        });
        
        if (!response.ok) {
            console.error('Failed to add issue to project');
        }
    }
    
    // Get project ID
    async getProjectId() {
        const query = `
            query($owner: String!, $repo: String!, $number: Int!) {
                repository(owner: $owner, name: $repo) {
                    projectV2(number: $number) {
                        id
                    }
                }
            }
        `;
        
        const response = await fetch(this.graphqlUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...this.getAuthHeader()
            },
            body: JSON.stringify({
                query,
                variables: {
                    owner: this.owner,
                    repo: this.repo,
                    number: this.projectNumber
                }
            })
        });
        
        const data = await response.json();
        return data.data?.repository?.projectV2?.id;
    }
    
    // Add reaction (vote)
    async addReaction(issueNumber, reaction) {
        if (!window.auth || !window.auth.isAuthenticated()) {
            throw new Error('Authentication required');
        }
        
        // First get issue node ID
        const issue = await this.fetchIssue(issueNumber);
        
        const mutation = `
            mutation($subjectId: ID!, $content: ReactionContent!) {
                addReaction(input: {
                    subjectId: $subjectId,
                    content: $content
                }) {
                    reaction {
                        id
                    }
                }
            }
        `;
        
        const response = await fetch(this.graphqlUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...this.getAuthHeader()
            },
            body: JSON.stringify({
                query: mutation,
                variables: {
                    subjectId: issue.node_id,
                    content: reaction // THUMBS_UP or THUMBS_DOWN
                }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to add reaction');
        }
        
        // Update local vote count
        this.updateVoteCount(issueNumber, reaction === 'THUMBS_UP' ? 1 : -1);
    }
    
    // Fetch single issue
    async fetchIssue(issueNumber) {
        const response = await fetch(
            `${this.baseUrl}/repos/${this.owner}/${this.repo}/issues/${issueNumber}`,
            {
                headers: {
                    'Accept': 'application/vnd.github.v3+json',
                    ...this.getAuthHeader()
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`Failed to fetch issue: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // Fetch completed papers
    async fetchCompletedPapers() {
        // For now, return mock data
        // In production, this would fetch from the papers directory
        return [];
    }
    
    // Extract keywords from issue
    extractKeywords(issue) {
        const keywords = [];
        
        // Extract from labels
        issue.labels.forEach(label => {
            if (!['status', 'score'].some(prefix => label.name.startsWith(prefix))) {
                keywords.push(label.name);
            }
        });
        
        // Extract from body (simple keyword extraction)
        const bodyKeywords = this.extractKeywordsFromText(issue.body || '');
        keywords.push(...bodyKeywords);
        
        return [...new Set(keywords)]; // Remove duplicates
    }
    
    // Simple keyword extraction
    extractKeywordsFromText(text) {
        const commonWords = new Set(['the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'some', 'few', 'more', 'most', 'other', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once']);
        
        const words = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 3 && !commonWords.has(word));
        
        // Get word frequency
        const wordFreq = {};
        words.forEach(word => {
            wordFreq[word] = (wordFreq[word] || 0) + 1;
        });
        
        // Return top keywords
        return Object.entries(wordFreq)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([word]) => word);
    }
    
    // View tracking (using localStorage)
    trackView(issueNumber) {
        const views = JSON.parse(localStorage.getItem(CONFIG.storage.viewsKey) || '{}');
        views[issueNumber] = (views[issueNumber] || 0) + 1;
        localStorage.setItem(CONFIG.storage.viewsKey, JSON.stringify(views));
        return views[issueNumber];
    }
    
    getViews(issueNumber) {
        const views = JSON.parse(localStorage.getItem(CONFIG.storage.viewsKey) || '{}');
        return views[issueNumber] || 0;
    }
    
    // Vote tracking (using localStorage + reactions)
    updateVoteCount(issueNumber, delta) {
        const votes = JSON.parse(localStorage.getItem(CONFIG.storage.votesKey) || '{}');
        if (!votes[issueNumber]) {
            votes[issueNumber] = { up: 0, down: 0 };
        }
        
        if (delta > 0) {
            votes[issueNumber].up += delta;
        } else {
            votes[issueNumber].down += Math.abs(delta);
        }
        
        localStorage.setItem(CONFIG.storage.votesKey, JSON.stringify(votes));
        return votes[issueNumber];
    }
    
    getVotes(issueNumber) {
        const votes = JSON.parse(localStorage.getItem(CONFIG.storage.votesKey) || '{}');
        return votes[issueNumber] || { up: 0, down: 0 };
    }
    
    // Cache management
    setCache(key, data) {
        const cache = {
            data,
            timestamp: Date.now()
        };
        sessionStorage.setItem(`${CONFIG.storage.cacheKey}_${key}`, JSON.stringify(cache));
    }
    
    getCache(key) {
        const cached = sessionStorage.getItem(`${CONFIG.storage.cacheKey}_${key}`);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp > CONFIG.storage.cacheExpiry) {
            sessionStorage.removeItem(`${CONFIG.storage.cacheKey}_${key}`);
            return null;
        }
        
        return data;
    }
    
    clearCache() {
        const keys = Object.keys(sessionStorage);
        keys.forEach(key => {
            if (key.startsWith(CONFIG.storage.cacheKey)) {
                sessionStorage.removeItem(key);
            }
        });
    }
}

// Initialize API
window.api = new GitHubAPI();