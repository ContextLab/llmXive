// Debug script to test project board fetching

async function debugProjectBoard() {
    console.log('=== DEBUGGING PROJECT BOARD ===');
    
    // Test 1: Direct GraphQL query
    const query = `
        query {
            organization(login: "ContextLab") {
                projectV2(number: 13) {
                    title
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
    
    try {
        console.log('Fetching project data...');
        const response = await fetch('https://api.github.com/graphql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json',
                // Try with a token if available
                ...(window.githubAuth?.token ? {
                    'Authorization': `Bearer ${window.githubAuth.token}`
                } : {})
            },
            body: JSON.stringify({ query })
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        
        if (data.errors) {
            console.error('GraphQL errors:', data.errors);
        }
        
        console.log('Full response:', data);
        
        // Parse the data
        const projectData = data.data?.organization?.projectV2;
        if (projectData) {
            console.log('Project title:', projectData.title);
            console.log('Total items:', projectData.items.nodes.length);
            
            // Look for issue #21 specifically
            const issue21 = projectData.items.nodes.find(item => 
                item.content?.number === 21
            );
            
            if (issue21) {
                console.log('\n=== ISSUE #21 ===');
                console.log('Title:', issue21.content.title);
                console.log('Field values:', issue21.fieldValues.nodes);
                
                const statusField = issue21.fieldValues.nodes.find(fv => 
                    fv.field?.name === 'Status'
                );
                console.log('Status field:', statusField);
                console.log('Status value:', statusField?.name);
            } else {
                console.log('Issue #21 not found in project');
            }
            
            // Show status distribution
            console.log('\n=== STATUS DISTRIBUTION ===');
            const statusCounts = {};
            projectData.items.nodes.forEach(item => {
                if (item.content?.number) {
                    const status = item.fieldValues.nodes.find(fv => 
                        fv.field?.name === 'Status'
                    )?.name || 'No Status';
                    statusCounts[status] = (statusCounts[status] || 0) + 1;
                }
            });
            console.table(statusCounts);
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Run the debug when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', debugProjectBoard);
} else {
    debugProjectBoard();
}