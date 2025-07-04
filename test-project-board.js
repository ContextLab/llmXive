// Test script to check project board status locally

const fetch = require('node-fetch');

async function testProjectBoardStatus(token) {
    console.log('Testing GitHub Project Board Status...\n');
    
    if (!token && !process.env.GITHUB_TOKEN) {
        console.error('No GitHub token provided. Please set GITHUB_TOKEN environment variable or pass token as argument.');
        console.log('\nTo create a token:');
        console.log('1. Go to https://github.com/settings/tokens/new');
        console.log('2. Select scopes: repo, read:project');
        console.log('3. Generate token and copy it');
        console.log('4. Run: GITHUB_TOKEN=your_token_here node test-project-board.js');
        return;
    }
    
    const authToken = token || process.env.GITHUB_TOKEN;
    console.log('Using authentication token:', authToken.substring(0, 8) + '...');
    
    const query = `
        query {
            organization(login: "ContextLab") {
                projectV2(number: 13) {
                    title
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2SingleSelectField {
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                    items(first: 100) {
                        nodes {
                            id
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
        const response = await fetch('https://api.github.com/graphql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            console.error('Response not OK:', response.status, response.statusText);
            const text = await response.text();
            console.error('Response body:', text);
            return;
        }
        
        const data = await response.json();
        
        if (data.errors) {
            console.error('GraphQL Errors:', JSON.stringify(data.errors, null, 2));
        }
        
        if (data.data?.organization?.projectV2) {
            const project = data.data.organization.projectV2;
            console.log(`Project: ${project.title}\n`);
            
            // Show available status options
            console.log('Available Status Options:');
            project.fields.nodes.forEach(field => {
                if (field.name === 'Status' && field.options) {
                    field.options.forEach(opt => {
                        console.log(`  - ${opt.name} (id: ${opt.id})`);
                    });
                }
            });
            console.log('');
            
            // Find specific issues
            const testIssues = [21, 1, 5, 10, 22, 23, 24];
            const items = project.items.nodes;
            
            console.log('Issue Statuses:');
            console.log('================');
            
            testIssues.forEach(issueNum => {
                const item = items.find(i => i.content?.number === issueNum);
                
                if (item) {
                    const statusField = item.fieldValues.nodes.find(
                        fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                              fv.field?.name === 'Status'
                    );
                    
                    console.log(`Issue #${issueNum}: ${statusField?.name || 'NO STATUS FOUND'}`);
                    
                    if (issueNum === 21) {
                        console.log(`  -> Expected: "In Progress", Got: "${statusField?.name || 'NO STATUS'}"`);
                        console.log(`  -> Field values:`, item.fieldValues.nodes.map(fv => ({
                            type: fv.__typename,
                            name: fv.name,
                            field: fv.field?.name
                        })));
                    }
                } else {
                    console.log(`Issue #${issueNum}: NOT IN PROJECT`);
                }
            });
            
            // Show overall distribution
            console.log('\nStatus Distribution:');
            console.log('==================');
            const distribution = {};
            
            items.forEach(item => {
                if (item.content?.number) {
                    const statusField = item.fieldValues.nodes.find(
                        fv => fv.__typename === 'ProjectV2ItemFieldSingleSelectValue' && 
                              fv.field?.name === 'Status'
                    );
                    const status = statusField?.name || 'NO STATUS';
                    distribution[status] = (distribution[status] || 0) + 1;
                }
            });
            
            Object.entries(distribution).forEach(([status, count]) => {
                console.log(`  ${status}: ${count} issues`);
            });
            
        } else {
            console.error('No project data found in response');
            console.log('Full response:', JSON.stringify(data, null, 2));
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Check if node-fetch is available
try {
    // Get token from command line args if provided
    const token = process.argv[2];
    testProjectBoardStatus(token);
} catch (e) {
    console.log('node-fetch not available, trying with native fetch...');
    // If running in a browser-like environment
    if (typeof fetch !== 'undefined') {
        testProjectBoardStatus();
    } else {
        console.error('No fetch implementation available');
    }
}