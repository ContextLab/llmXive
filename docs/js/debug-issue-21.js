// Debug script to trace issue #21 through the system
(function() {
    console.log('%c=== DEBUG ISSUE #21 ===', 'color: blue; font-weight: bold');
    
    // Wait for API to be available
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
    
    async function debugIssue21() {
        // Wait for everything to load
        await waitFor(() => window.api && window.ui && window.ui.projects);
        
        console.log('Starting debug...');
        
        // Find issue 21 in the projects
        const issue21 = window.ui.projects.find(p => p.number === 21);
        
        if (issue21) {
            console.log('%cFound Issue #21:', 'color: green; font-weight: bold');
            console.log('- Title:', issue21.title);
            console.log('- Labels:', issue21.labels.map(l => l.name));
            console.log('- Project Status:', issue21.projectStatus);
            console.log('- Full issue object:', issue21);
        } else {
            console.log('%cIssue #21 NOT FOUND in projects array!', 'color: red; font-weight: bold');
            console.log('Total projects loaded:', window.ui.projects.length);
            console.log('Project numbers:', window.ui.projects.map(p => p.number).sort((a,b) => a-b));
        }
        
        // Check filtered projects
        if (window.ui.filteredProjects) {
            const filtered21 = window.ui.filteredProjects.find(p => p.number === 21);
            if (filtered21) {
                console.log('%cIssue #21 in filtered projects:', 'color: blue');
                console.log('- Project Status:', filtered21.projectStatus);
            } else {
                console.log('%cIssue #21 NOT in filtered projects', 'color: orange');
            }
        }
        
        // Check the DOM
        console.log('\n%cChecking DOM...', 'color: purple; font-weight: bold');
        const allCards = document.querySelectorAll('.project-card');
        let foundInDOM = false;
        
        allCards.forEach(card => {
            const titleEl = card.querySelector('.project-title');
            if (titleEl && titleEl.textContent.includes('#21')) {
                foundInDOM = true;
                const column = card.closest('.projects-column');
                const columnTitle = column ? column.querySelector('.column-header h3').textContent : 'Unknown';
                console.log('%cIssue #21 found in DOM:', 'color: green');
                console.log('- In column:', columnTitle);
                console.log('- Card element:', card);
            }
        });
        
        if (!foundInDOM) {
            console.log('%cIssue #21 NOT found in DOM', 'color: red');
        }
        
        // Test the GraphQL query directly
        console.log('\n%cTesting GraphQL query...', 'color: blue; font-weight: bold');
        const query = `
            query {
                organization(login: "ContextLab") {
                    projectV2(number: 13) {
                        items(first: 100) {
                            nodes {
                                content {
                                    ... on Issue {
                                        number
                                        title
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
            };
            
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            
            if (data.data?.organization?.projectV2?.items?.nodes) {
                const issue21Data = data.data.organization.projectV2.items.nodes.find(
                    item => item.content?.number === 21
                );
                
                if (issue21Data) {
                    const statusField = issue21Data.fieldValues.nodes.find(
                        fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                              fv.field?.name === 'Status'
                    );
                    console.log('%cGraphQL result for Issue #21:', 'color: green');
                    console.log('- Title:', issue21Data.content.title);
                    console.log('- Status:', statusField?.name || 'NO STATUS');
                } else {
                    console.log('%cIssue #21 not in GraphQL results', 'color: red');
                }
            }
        } catch (error) {
            console.error('GraphQL error:', error);
        }
    }
    
    // Run debug after a delay
    setTimeout(debugIssue21, 3000);
    
    // Also add a button to re-run debug
    window.debugIssue21 = debugIssue21;
    console.log('You can run window.debugIssue21() to debug again');
})();