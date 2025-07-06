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
    
    // Fetch file content from GitHub
    async fetchFileContent(path) {
        try {
            const response = await fetch(
                `https://api.github.com/repos/${this.owner}/${this.repo}/contents/${path}`,
                { headers: this.getHeaders() }
            );
            
            if (!response.ok) {
                throw new Error(`Failed to fetch ${path}: ${response.status}`);
            }
            
            const data = await response.json();
            // Decode base64 content
            return atob(data.content);
        } catch (error) {
            console.error(`Error fetching file ${path}:`, error);
            throw error;
        }
    }
    
    // Parse markdown table into structured data
    parseMarkdownTable(markdown, tableHeader) {
        const lines = markdown.split('\n');
        let tableStart = -1;
        let headers = [];
        
        // Find the table header
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes(tableHeader)) {
                // Look for the actual table starting after this header
                for (let j = i; j < lines.length; j++) {
                    if (lines[j].startsWith('|') && lines[j].includes('|')) {
                        headers = lines[j].split('|').map(h => h.trim()).filter(h => h);
                        tableStart = j + 2; // Skip separator line
                        break;
                    }
                }
                break;
            }
        }
        
        if (tableStart === -1) {
            console.warn(`Table with header "${tableHeader}" not found`);
            return [];
        }
        
        const rows = [];
        for (let i = tableStart; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line || !line.startsWith('|')) break;
            
            const cells = line.split('|').map(c => c.trim()).filter(c => c);
            if (cells.length >= headers.length) {
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = cells[index] || '';
                });
                rows.push(row);
            }
        }
        
        return rows;
    }
    
    // Load papers from README
    async loadPapers() {
        try {
            const readme = await this.fetchFileContent('papers/README.md');
            
            const completed = this.parseMarkdownTable(readme, 'Completed work');
            const inProgress = this.parseMarkdownTable(readme, 'In-progress work');
            
            return {
                completed: completed.map(paper => ({
                    id: paper['Project ID'] || paper.ID,
                    title: paper.Title || paper.Paper,
                    authors: paper.Authors || paper.Contributors || '',
                    status: 'completed',
                    paperUrl: this.extractLinkFromMarkdown(paper.Paper || paper.Title),
                    codeUrl: paper.Code ? this.extractLinkFromMarkdown(paper.Code) : null,
                    dataUrl: paper.Data ? this.extractLinkFromMarkdown(paper.Data) : null,
                    type: 'paper'
                })),
                inProgress: inProgress.map(paper => ({
                    id: paper['Project ID'] || paper.ID,
                    title: paper.Title || paper.Paper,
                    authors: paper.Authors || paper.Contributors || '',
                    status: 'in-progress',
                    paperUrl: this.extractLinkFromMarkdown(paper.Paper || paper.Title),
                    codeUrl: paper.Code ? this.extractLinkFromMarkdown(paper.Code) : null,
                    dataUrl: paper.Data ? this.extractLinkFromMarkdown(paper.Data) : null,
                    type: 'paper'
                }))
            };
        } catch (error) {
            console.error('Error loading papers:', error);
            return { completed: [], inProgress: [] };
        }
    }
    
    // Load implementation plans from README
    async loadImplementationPlans() {
        try {
            const readme = await this.fetchFileContent('implementation_plans/README.md');
            const plans = this.parseMarkdownTable(readme, 'Table of Contents');
            
            return plans.map(plan => ({
                id: plan['Unique ID'] || plan.ID,
                title: plan['Project Name'] || plan.Title,
                author: plan['Contributor(s)'] || plan.Contributors || plan.Author,
                date: null, // No date column in current table
                issueUrl: this.extractLinkFromMarkdown(plan['Link(s) to GitHub issues'] || plan.Issue),
                planUrl: this.extractLinkFromMarkdown(plan['Link to implementation plan'] || plan.Plan),
                status: plan['Current Status'] || 'ready',
                type: 'plan'
            }));
        } catch (error) {
            console.error('Error loading implementation plans:', error);
            return [];
        }
    }
    
    // Load technical design documents from README
    async loadTechnicalDesigns() {
        try {
            const readme = await this.fetchFileContent('technical_design_documents/README.md');
            const designs = this.parseMarkdownTable(readme, 'Table of Contents');
            
            return designs.map(design => ({
                id: design['Unique ID'] || design.ID,
                title: design['Project Name'] || design.Title,
                author: design['Contributors'] || design.Author,
                date: null, // No date column in current table
                issueUrl: this.extractLinkFromMarkdown(design['Link(s) to GitHub issues'] || design.Issue),
                designUrl: this.extractLinkFromMarkdown(design['Link to technical design document'] || design.Design),
                status: design['Current Status'] || 'design',
                type: 'design'
            }));
        } catch (error) {
            console.error('Error loading technical designs:', error);
            return [];
        }
    }
    
    // Load reviews from README
    async loadReviews() {
        try {
            const readme = await this.fetchFileContent('reviews/README.md');
            const reviews = this.parseMarkdownTable(readme, 'Table of Contents');
            
            return reviews.map(review => ({
                id: review['Project ID'] || review.ID,
                reviewer: review.Reviewer || review.Author,
                date: review.Date,
                type: review.Type || review['Review Type'],
                reviewUrl: this.extractLinkFromMarkdown(review.Review || review['Review File']),
                projectId: review['Project ID'] || review.ID
            }));
        } catch (error) {
            console.error('Error loading reviews:', error);
            return [];
        }
    }
    
    // Extract URL from markdown link format [text](url)
    extractLinkFromMarkdown(text) {
        if (!text) return null;
        const match = text.match(/\[.*?\]\((.*?)\)/);
        return match ? match[1] : null;
    }
    
    // Load contributors aggregated from all README tables
    async loadContributors() {
        try {
            const contributors = new Map();
            
            // Get contributors from backlog (GitHub issues)
            const issues = await this.fetchProjectIssues();
            issues.forEach(issue => {
                if (issue.realAuthor) {
                    const name = issue.realAuthor.name;
                    if (!contributors.has(name)) {
                        contributors.set(name, {
                            name: name,
                            type: issue.realAuthor.type,
                            avatar: issue.realAuthor.type === 'human' ? issue.user.avatar_url : null,
                            areas: new Set(),
                            contributions: []
                        });
                    }
                    contributors.get(name).areas.add('Ideas');
                    contributors.get(name).contributions.push({
                        type: 'idea',
                        title: issue.title,
                        url: issue.html_url,
                        date: issue.created_at
                    });
                }
            });
            
            // Get contributors from papers
            const papersData = await this.loadPapers();
            [...papersData.completed, ...papersData.inProgress].forEach(paper => {
                if (paper.authors) {
                    const authors = paper.authors.split(',').map(a => a.trim());
                    authors.forEach(author => {
                        if (!contributors.has(author)) {
                            contributors.set(author, {
                                name: author,
                                type: this.isHumanAuthor(author) ? 'human' : 'ai',
                                avatar: null,
                                areas: new Set(),
                                contributions: []
                            });
                        }
                        contributors.get(author).areas.add('Papers');
                        contributors.get(author).contributions.push({
                            type: 'paper',
                            title: paper.title,
                            url: paper.paperUrl,
                            date: null,
                            status: paper.status
                        });
                    });
                }
            });
            
            // Get contributors from technical designs
            const designs = await this.loadTechnicalDesigns();
            designs.forEach(design => {
                if (design.author) {
                    const authors = design.author.split(',').map(a => a.trim());
                    authors.forEach(author => {
                        if (!contributors.has(author)) {
                            contributors.set(author, {
                                name: author,
                                type: this.isHumanAuthor(author) ? 'human' : 'ai',
                                avatar: null,
                                areas: new Set(),
                                contributions: []
                            });
                        }
                        contributors.get(author).areas.add('Designs');
                        contributors.get(author).contributions.push({
                            type: 'design',
                            title: design.title,
                            url: design.designUrl,
                            date: null
                        });
                    });
                }
            });
            
            // Get contributors from implementation plans
            const plans = await this.loadImplementationPlans();
            plans.forEach(plan => {
                if (plan.author) {
                    const authors = plan.author.split(',').map(a => a.trim());
                    authors.forEach(author => {
                        if (!contributors.has(author)) {
                            contributors.set(author, {
                                name: author,
                                type: this.isHumanAuthor(author) ? 'human' : 'ai',
                                avatar: null,
                                areas: new Set(),
                                contributions: []
                            });
                        }
                        contributors.get(author).areas.add('Implementations');
                        contributors.get(author).contributions.push({
                            type: 'plan',
                            title: plan.title,
                            url: plan.planUrl,
                            date: null
                        });
                    });
                }
            });
            
            // Get contributors from reviews
            const reviews = await this.loadReviews();
            reviews.forEach(review => {
                if (review.reviewer) {
                    const name = review.reviewer;
                    if (!contributors.has(name)) {
                        contributors.set(name, {
                            name: name,
                            type: this.isHumanAuthor(name) ? 'human' : 'ai',
                            avatar: null,
                            areas: new Set(),
                            contributions: []
                        });
                    }
                    contributors.get(name).areas.add('Reviews');
                    contributors.get(name).contributions.push({
                        type: 'review',
                        title: `${review.type} Review`,
                        url: review.reviewUrl,
                        date: review.date,
                        reviewType: review.type
                    });
                }
            });
            
            // Convert to array and sort by contribution count
            const contributorsArray = Array.from(contributors.values()).map(contributor => ({
                ...contributor,
                areas: Array.from(contributor.areas),
                totalContributions: contributor.contributions.length
            })).sort((a, b) => b.totalContributions - a.totalContributions);
            
            return contributorsArray;
            
        } catch (error) {
            console.error('Error loading contributors:', error);
            return [];
        }
    }
    
    // Create a new file in the repository
    async createFile(path, content, commitMessage) {
        if (!window.githubAuth || !window.githubAuth.isAuthenticated()) {
            throw new Error('Authentication required');
        }
        
        try {
            const response = await fetch(
                `${this.baseUrl}/repos/${this.owner}/${this.repo}/contents/${path}`,
                {
                    method: 'PUT',
                    headers: this.getHeaders(),
                    body: JSON.stringify({
                        message: commitMessage,
                        content: btoa(content), // base64 encode
                        branch: 'main'
                    })
                }
            );
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to create file');
            }
            
            const result = await response.json();
            console.log('File created successfully:', result);
            return result;
            
        } catch (error) {
            console.error('Error creating file:', error);
            throw error;
        }
    }
}

// Initialize API
window.api = new GitHubAPI();