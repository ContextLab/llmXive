// Netlify Function for GitHub OAuth
// This keeps the client_secret secure on the server side

exports.handler = async (event, context) => {
    // Only allow POST
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }
    
    try {
        const { code } = JSON.parse(event.body);
        
        if (!code) {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'Code required' })
            };
        }
        
        // Exchange code for token
        const response = await fetch('https://github.com/login/oauth/access_token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                client_id: process.env.GITHUB_CLIENT_ID,
                client_secret: process.env.GITHUB_CLIENT_SECRET,
                code: code
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: data.error_description })
            };
        }
        
        // Return the access token
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                access_token: data.access_token,
                token_type: data.token_type,
                scope: data.scope
            })
        };
        
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Internal server error' })
        };
    }
};