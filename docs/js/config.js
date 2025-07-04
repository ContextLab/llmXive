// Configuration
const CONFIG = {
    github: {
        owner: 'ContextLab',
        repo: 'llmXive',
        projectNumber: 13
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