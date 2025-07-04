// Debug GraphQL errors
(function() {
    console.log('%c=== DEBUGGING GRAPHQL ERRORS ===', 'color: red; font-weight: bold');
    
    async function debugGraphQL() {
        // Try the simplest possible query first
        const simpleQuery = `
            query {
                viewer {
                    login
                }
            }
        `;
        
        try {
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json'
            };
            
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
                console.log('Using auth headers');
            }
            
            console.log('Testing simple query...');
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query: simpleQuery })
            });
            
            const data = await response.json();
            console.log('Simple query result:', data);
            
            if (data.errors) {
                console.error('GraphQL errors:', data.errors.map(e => ({
                    message: e.message,
                    type: e.type,
                    path: e.path
                })));
            }
            
        } catch (error) {
            console.error('Request error:', error);
        }
        
        // Now try the project query with better error handling
        const projectQuery = `
            query {
                repository(owner: "ContextLab", name: "llmXive") {
                    issue(number: 21) {
                        number
                        title
                        projectItems(first: 10) {
                            nodes {
                                id
                            }
                        }
                    }
                }
            }
        `;
        
        try {
            console.log('\nTesting project query for issue 21...');
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json'
            };
            
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query: projectQuery })
            });
            
            const data = await response.json();
            console.log('Project query result:', data);
            
            if (data.errors) {
                console.error('Project query errors:', data.errors);
            }
            
        } catch (error) {
            console.error('Project query error:', error);
        }
    }
    
    // Run after a delay
    setTimeout(debugGraphQL, 1500);
    
    window.debugGraphQL = debugGraphQL;
})();