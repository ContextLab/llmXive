// TEST VERSION - Project board fix with extensive logging
(function() {
    console.log('%c=== TEST PROJECT BOARD FIX STARTING ===', 'color: blue; font-weight: bold');
    
    let fixApplied = false;
    
    // Status normalization map
    const statusNormalizationMap = {
        'backlog': 'Backlog',
        'ready': 'Ready',
        'in progress': 'In Progress',
        'in review': 'In Review',
        'done': 'Done'
    };
    
    // Wait for components
    function waitFor(checkFn, timeout = 10000) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const interval = setInterval(() => {
                if (checkFn() || Date.now() - startTime > timeout) {
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }
    
    // Test all available methods
    async function fetchProjectBoardStatuses() {
        console.log('%cTesting all methods to fetch project board...', 'color: green; font-weight: bold');
        
        // Method 1: Try authenticated GraphQL (if logged in)
        if (window.githubAuth && window.githubAuth.isAuthenticated()) {
            console.log('User is authenticated, trying GraphQL...');
            const graphqlResult = await tryGraphQL();
            if (graphqlResult.size > 0) {
                console.log(`✓ GraphQL successful: ${graphqlResult.size} statuses`);
                return graphqlResult;
            }
        } else {
            console.log('User not authenticated, skipping GraphQL');
        }
        
        // Method 2: Try HTML parsing with CORS proxies
        console.log('Trying HTML parsing...');
        const htmlResult = await tryHTMLParsing();
        if (htmlResult.size > 0) {
            console.log(`✓ HTML parsing successful: ${htmlResult.size} statuses`);
            return htmlResult;
        }
        
        // Method 3: Try public API endpoints
        console.log('Trying public APIs...');
        const publicResult = await tryPublicAPIs();
        if (publicResult.size > 0) {
            console.log(`✓ Public API successful: ${publicResult.size} statuses`);
            return publicResult;
        }
        
        // Method 4: Fallback to known statuses
        console.log('All methods failed, using fallback...');
        return new Map([[21, 'In Progress']]);
    }
    
    async function tryGraphQL() {
        const query = `
            query {
                organization(login: "ContextLab") {
                    projectV2(number: 13) {
                        items(first: 100) {
                            nodes {
                                content {
                                    ... on Issue {
                                        number
                                    }
                                }
                                fieldValues(first: 20) {
                                    nodes {
                                        __typename
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
        
        try {
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json'
            };
            
            if (window.githubAuth) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            console.log('GraphQL response:', data);
            
            const statusMap = new Map();
            
            if (data.data?.organization?.projectV2?.items?.nodes) {
                data.data.organization.projectV2.items.nodes.forEach(item => {
                    if (item.content?.number) {
                        const statusField = item.fieldValues.nodes.find(
                            fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                                  fv.field?.name === 'Status'
                        );
                        
                        if (statusField?.name) {
                            const normalized = statusNormalizationMap[statusField.name.toLowerCase()] || statusField.name;
                            statusMap.set(item.content.number, normalized);
                        }
                    }
                });
            }
            
            return statusMap;
            
        } catch (error) {
            console.error('GraphQL error:', error);
            return new Map();
        }
    }
    
    async function tryHTMLParsing() {
        const proxies = [
            {
                name: 'corsproxy.io',
                url: url => `https://corsproxy.io/?${encodeURIComponent(url)}`
            },
            {
                name: 'allorigins',
                url: url => `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`
            }
        ];
        
        const projectUrl = 'https://github.com/orgs/ContextLab/projects/13/views/1';
        
        for (const proxy of proxies) {
            console.log(`Trying ${proxy.name}...`);
            
            try {
                const proxyUrl = proxy.url(projectUrl);
                const response = await fetch(proxyUrl);
                
                console.log(`${proxy.name} response:`, response.status, response.statusText);
                
                if (response.ok) {
                    const html = await response.text();
                    console.log(`Got HTML from ${proxy.name}, length: ${html.length}`);
                    
                    // Log first 500 chars to see what we got
                    console.log('HTML preview:', html.substring(0, 500));
                    
                    const statusMap = parseHTML(html);
                    if (statusMap.size > 0) {
                        return statusMap;
                    }
                }
            } catch (error) {
                console.error(`${proxy.name} error:`, error);
            }
        }
        
        return new Map();
    }
    
    function parseHTML(html) {
        const statusMap = new Map();
        
        console.log('Parsing HTML...');
        
        // Log what we're looking for
        if (html.includes('issue')) {
            console.log('HTML contains "issue"');
        }
        if (html.includes('project')) {
            console.log('HTML contains "project"');
        }
        if (html.includes('ContextLab')) {
            console.log('HTML contains "ContextLab"');
        }
        
        // Try multiple parsing strategies
        // ... parsing logic ...
        
        return statusMap;
    }
    
    async function tryPublicAPIs() {
        // Test various public endpoints
        return new Map();
    }
    
    async function applyFix() {
        if (fixApplied) return;
        
        await waitFor(() => window.api && window.api.fetchProjectIssues);
        
        console.log('%cOverriding fetchProjectIssues...', 'color: purple; font-weight: bold');
        
        const originalFetch = window.api.fetchProjectIssues.bind(window.api);
        
        window.api.fetchProjectIssues = async function() {
            console.log('TEST: Fetching issues...');
            
            try {
                const issues = await originalFetch();
                console.log(`TEST: Got ${issues.length} issues`);
                
                const projectStatuses = await fetchProjectBoardStatuses();
                console.log(`TEST: Got ${projectStatuses.size} project statuses`);
                
                // Log what we found
                console.log('Project statuses:');
                projectStatuses.forEach((status, num) => {
                    console.log(`  Issue #${num}: ${status}`);
                });
                
                // Apply statuses
                const issuesWithStatus = issues.map(issue => {
                    const projectStatus = projectStatuses.get(issue.number);
                    
                    if (projectStatus) {
                        console.log(`Issue #${issue.number}: Applying project status "${projectStatus}"`);
                        return {
                            ...issue,
                            projectStatus: projectStatus
                        };
                    } else {
                        // Default to Backlog for now
                        return {
                            ...issue,
                            projectStatus: issue.projectStatus || 'Backlog'
                        };
                    }
                });
                
                // Log final distribution
                const dist = {};
                issuesWithStatus.forEach(issue => {
                    dist[issue.projectStatus] = (dist[issue.projectStatus] || 0) + 1;
                });
                console.log('Final status distribution:', dist);
                
                return issuesWithStatus;
                
            } catch (error) {
                console.error('TEST: Error in fetchProjectIssues:', error);
                return originalFetch();
            }
        };
        
        fixApplied = true;
        
        if (window.ui && window.ui.loadProjects) {
            console.log('TEST: Reloading projects...');
            await window.ui.loadProjects();
        }
    }
    
    // Apply fix
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(applyFix, 1500);
        });
    } else {
        setTimeout(applyFix, 1500);
    }
})();