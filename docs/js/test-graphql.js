// Simple test of GraphQL query
(function() {
    console.log('%c=== TESTING GRAPHQL DIRECTLY ===', 'color: purple; font-weight: bold');
    
    async function testGraphQL() {
        const query = `
            query {
                repository(owner: "ContextLab", name: "llmXive") {
                    issues(first: 100, states: OPEN) {
                        nodes {
                            number
                            title
                            projectItems(first: 10) {
                                nodes {
                                    project {
                                        title
                                        number
                                    }
                                    fieldValues(first: 10) {
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
            }
        `;
        
        try {
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json'
            };
            
            if (window.githubAuth && window.githubAuth.isAuthenticated()) {
                Object.assign(headers, window.githubAuth.getAuthHeaders());
                console.log('Using auth for GraphQL');
            }
            
            const response = await fetch('https://api.github.com/graphql', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ query })
            });
            
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.data?.repository?.issues?.nodes) {
                const issue21 = data.data.repository.issues.nodes.find(i => i.number === 21);
                if (issue21) {
                    console.log('%cIssue #21 found:', 'color: green; font-weight: bold');
                    console.log('Title:', issue21.title);
                    console.log('Project items:', issue21.projectItems.nodes);
                    
                    issue21.projectItems.nodes.forEach(item => {
                        console.log('Project:', item.project.title);
                        const statusField = item.fieldValues.nodes.find(
                            fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                                  fv.field?.name === 'Status'
                        );
                        console.log('Status:', statusField?.name || 'NO STATUS');
                    });
                }
            }
            
        } catch (error) {
            console.error('GraphQL test error:', error);
        }
    }
    
    // Run test after a delay
    setTimeout(testGraphQL, 2000);
    
    window.testGraphQL = testGraphQL;
})();