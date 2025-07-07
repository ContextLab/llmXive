/**
 * Netlify Function for OAuth Token Exchange
 * 
 * Securely handles GitHub OAuth token exchange server-side
 * to protect client secret from exposure in browser code.
 */

export const handler = async (event, context) => {
    // Enable CORS
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    };
    
    // Handle preflight requests
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }
    
    // Only allow POST requests
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }
    
    try {
        const { code, codeVerifier } = JSON.parse(event.body);
        
        if (!code || !codeVerifier) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Missing required parameters' })
            };
        }
        
        // GitHub OAuth token exchange
        const tokenResponse = await fetch('https://github.com/login/oauth/access_token', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'llmXive-v2.0'
            },
            body: JSON.stringify({
                client_id: process.env.GITHUB_CLIENT_ID,
                client_secret: process.env.GITHUB_CLIENT_SECRET,
                code: code,
                code_verifier: codeVerifier
            })
        });
        
        if (!tokenResponse.ok) {
            console.error('GitHub OAuth failed:', tokenResponse.status, tokenResponse.statusText);
            return {
                statusCode: 500,
                headers,
                body: JSON.stringify({ error: 'OAuth exchange failed' })
            };
        }
        
        const tokenData = await tokenResponse.json();
        
        if (tokenData.error) {
            console.error('GitHub OAuth error:', tokenData.error_description);
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: tokenData.error_description })
            };
        }
        
        // Return the token data (without exposing client secret)
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                access_token: tokenData.access_token,
                token_type: tokenData.token_type,
                expires_in: tokenData.expires_in,
                scope: tokenData.scope
            })
        };
        
    } catch (error) {
        console.error('OAuth exchange error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Internal server error' })
        };
    }
};