// Configuration
const CONFIG = {
    github: {
        owner: 'ContextLab',
        repo: 'llmXive',
        projectNumber: 13,
        // Note: For production, use a GitHub App or OAuth flow
        // This is a read-only token for demo purposes
        token: null // Will be set via environment or user input
    },
    
    api: {
        baseUrl: 'https://api.github.com',
        graphqlUrl: 'https://api.github.com/graphql',
        perPage: 100
    },
    
    storage: {
        viewsKey: 'llmxive_views',
        votesKey: 'llmxive_votes',
        cacheKey: 'llmxive_cache',
        cacheExpiry: 5 * 60 * 1000 // 5 minutes
    },
    
    ui: {
        debounceDelay: 300,
        animationDuration: 300,
        maxDescriptionLength: 200
    },
    
    // Map GitHub labels to status
    statusMap: {
        'backlog': 'Backlog',
        'ready': 'Ready',
        'in-progress': 'In progress',
        'in-review': 'In review',
        'done': 'Done'
    },
    
    // Status colors
    statusColors: {
        'Backlog': '#6b7280',
        'Ready': '#3b82f6',
        'In progress': '#f59e0b',
        'In review': '#8b5cf6',
        'Done': '#10b981'
    }
};

// Initialize configuration from URL parameters or localStorage
function initializeConfig() {
    // Check for token in URL params (for demo/testing)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenParam = urlParams.get('token');
    
    if (tokenParam) {
        CONFIG.github.token = tokenParam;
        // Remove token from URL for security
        urlParams.delete('token');
        const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
        window.history.replaceState({}, '', newUrl);
    }
    
    // Check localStorage for saved token
    const savedToken = localStorage.getItem('github_token');
    if (savedToken && !CONFIG.github.token) {
        CONFIG.github.token = savedToken;
    }
}

// Save configuration
function saveConfig() {
    if (CONFIG.github.token) {
        localStorage.setItem('github_token', CONFIG.github.token);
    }
}

// Initialize on load
initializeConfig();