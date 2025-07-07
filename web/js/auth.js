/**
 * Authentication Manager for llmXive
 * Handles OAuth flow, user state, and authentication UI
 */

import { EventTarget } from './events.js';
import { NotificationManager } from './utils.js';

export class AuthManager extends EventTarget {
    constructor(client, notifications) {
        super();
        
        this.client = client;
        this.notifications = notifications || new NotificationManager();
        this.authenticated = false;
        this.user = null;
        this.permissions = null;
        this.initPromise = null;
        
        // Bind methods
        this.handleAuthCallback = this.handleAuthCallback.bind(this);
        this.startAuthFlow = this.startAuthFlow.bind(this);
        this.logout = this.logout.bind(this);
        
        // Listen for auth callback on page load
        this.checkForAuthCallback();
    }
    
    /**
     * Initialize authentication
     */
    async initialize() {
        if (this.initPromise) {
            return this.initPromise;
        }
        
        this.initPromise = this._initialize();
        return this.initPromise;
    }
    
    async _initialize() {
        try {
            console.log('Initializing authentication...');
            
            // Check for stored authentication
            const storedAuth = this.getStoredAuth();
            
            if (storedAuth && this.isTokenValid(storedAuth)) {
                console.log('Found valid stored authentication');
                
                this.authenticated = true;
                this.user = storedAuth.user;
                this.permissions = storedAuth.permissions;
                
                // Verify token is still valid with GitHub
                try {
                    await this.verifyToken(storedAuth.token);
                    console.log('Token verified with GitHub');
                    
                    this.emit('authStateChange', {
                        authenticated: true,
                        user: this.user,
                        permissions: this.permissions
                    });
                    
                    return { authenticated: true };
                    
                } catch (error) {
                    console.warn('Stored token is invalid:', error);
                    this.clearAuth();
                }
            }
            
            console.log('No valid authentication found');
            this.emit('authStateChange', { authenticated: false });
            return { authenticated: false };
            
        } catch (error) {
            console.error('Authentication initialization failed:', error);
            this.emit('authStateChange', { 
                authenticated: false, 
                error: error.message 
            });
            return { authenticated: false, error: error.message };
        }
    }
    
    /**
     * Check for OAuth callback parameters
     */
    checkForAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        
        if (error) {
            console.error('OAuth error:', error);
            this.notifications.error(`Authentication failed: ${error}`);
            this.cleanupUrl();
            return;
        }
        
        if (code && state) {
            console.log('OAuth callback detected');
            this.handleAuthCallback(code, state);
        }
    }
    
    /**
     * Start OAuth authentication flow
     */
    async startAuthFlow() {
        try {
            console.log('Starting OAuth flow...');
            
            // Generate PKCE parameters
            const codeVerifier = this.generateCodeVerifier();
            const codeChallenge = await this.generateCodeChallenge(codeVerifier);
            const state = this.generateState();
            
            // Store PKCE parameters
            sessionStorage.setItem('oauth_code_verifier', codeVerifier);
            sessionStorage.setItem('oauth_state', state);
            
            // Build authorization URL
            const clientId = 'Ov23liY5hzeo5JVmlzcH';\n            const redirectUri = window.location.origin + window.location.pathname;\n            const scope = 'repo read:user';\n            \n            const authUrl = new URL('https://github.com/login/oauth/authorize');\n            authUrl.searchParams.set('client_id', clientId);\n            authUrl.searchParams.set('redirect_uri', redirectUri);\n            authUrl.searchParams.set('scope', scope);\n            authUrl.searchParams.set('state', state);\n            authUrl.searchParams.set('code_challenge', codeChallenge);\n            authUrl.searchParams.set('code_challenge_method', 'S256');\n            \n            console.log('Redirecting to GitHub for authentication...');\n            window.location.href = authUrl.toString();\n            \n        } catch (error) {\n            console.error('Failed to start OAuth flow:', error);\n            this.notifications.error('Failed to start authentication');\n        }\n    }\n    \n    /**\n     * Handle OAuth callback\n     */\n    async handleAuthCallback(code, state) {\n        try {\n            console.log('Handling OAuth callback...');\n            \n            // Verify state parameter\n            const storedState = sessionStorage.getItem('oauth_state');\n            if (state !== storedState) {\n                throw new Error('Invalid state parameter - possible CSRF attack');\n            }\n            \n            // Get code verifier\n            const codeVerifier = sessionStorage.getItem('oauth_code_verifier');\n            if (!codeVerifier) {\n                throw new Error('No code verifier found');\n            }\n            \n            this.notifications.info('Exchanging code for token...');\n            \n            // Exchange code for token\n            const tokenData = await this.exchangeCodeForToken(code, codeVerifier);\n            \n            // Store authentication data\n            await this.storeAuth(tokenData);\n            \n            // Clean up\n            sessionStorage.removeItem('oauth_code_verifier');\n            sessionStorage.removeItem('oauth_state');\n            this.cleanupUrl();\n            \n            this.notifications.success('Authentication successful!');\n            \n            // Emit auth state change\n            this.emit('authStateChange', {\n                authenticated: true,\n                user: this.user,\n                permissions: this.permissions\n            });\n            \n        } catch (error) {\n            console.error('OAuth callback failed:', error);\n            this.notifications.error(`Authentication failed: ${error.message}`);\n            \n            // Clean up on error\n            sessionStorage.removeItem('oauth_code_verifier');\n            sessionStorage.removeItem('oauth_state');\n            this.cleanupUrl();\n            \n            this.emit('authStateChange', { \n                authenticated: false, \n                error: error.message \n            });\n        }\n    }\n    \n    /**\n     * Exchange authorization code for access token\n     */\n    async exchangeCodeForToken(code, codeVerifier) {\n        // Use existing Heroku proxy\n        const proxyUrl = 'https://llmxive-auth-b300c94fab60.herokuapp.com/authenticate/';\n        \n        try {\n            const response = await fetch(proxyUrl + code, {\n                method: 'GET',\n                headers: {\n                    'Accept': 'application/json'\n                }\n            });\n            \n            if (!response.ok) {\n                throw new Error(`HTTP ${response.status}: ${response.statusText}`);\n            }\n            \n            const data = await response.json();\n            \n            if (data.error) {\n                throw new Error(`OAuth error: ${data.error}`);\n            }\n            \n            return {\n                access_token: data.token || data.access_token,\n                token_type: data.token_type || 'bearer',\n                expires_in: data.expires_in,\n                scope: data.scope\n            };\n            \n        } catch (error) {\n            console.error('Token exchange failed:', error);\n            throw new Error(`Failed to exchange code for token: ${error.message}`);\n        }\n    }\n    \n    /**\n     * Store authentication data\n     */\n    async storeAuth(tokenData) {\n        const token = tokenData.access_token;\n        const tokenExpiry = Date.now() + (tokenData.expires_in * 1000);\n        \n        try {\n            // Get user information\n            const userResponse = await fetch('https://api.github.com/user', {\n                headers: {\n                    'Authorization': `Bearer ${token}`,\n                    'Accept': 'application/vnd.github.v3+json'\n                }\n            });\n            \n            if (!userResponse.ok) {\n                throw new Error('Failed to fetch user information');\n            }\n            \n            const user = await userResponse.json();\n            \n            // Get repository permissions\n            let permissions = null;\n            try {\n                const permsResponse = await fetch('https://api.github.com/repos/ContextLab/llmXive', {\n                    headers: {\n                        'Authorization': `Bearer ${token}`,\n                        'Accept': 'application/vnd.github.v3+json'\n                    }\n                });\n                \n                if (permsResponse.ok) {\n                    const repoData = await permsResponse.json();\n                    permissions = repoData.permissions;\n                }\n            } catch (error) {\n                console.warn('Failed to fetch repository permissions:', error);\n            }\n            \n            // Update instance state\n            this.authenticated = true;\n            this.user = user;\n            this.permissions = permissions;\n            \n            // Store in localStorage\n            const authData = {\n                token,\n                user,\n                permissions,\n                expiry: tokenExpiry,\n                stored: Date.now()\n            };\n            \n            localStorage.setItem('llmxive_auth', JSON.stringify(authData));\n            \n            console.log('Authentication data stored successfully');\n            \n        } catch (error) {\n            console.error('Failed to store auth data:', error);\n            throw error;\n        }\n    }\n    \n    /**\n     * Get stored authentication data\n     */\n    getStoredAuth() {\n        try {\n            const stored = localStorage.getItem('llmxive_auth');\n            return stored ? JSON.parse(stored) : null;\n        } catch (error) {\n            console.error('Error reading stored auth:', error);\n            return null;\n        }\n    }\n    \n    /**\n     * Check if token is valid\n     */\n    isTokenValid(authData) {\n        if (!authData || !authData.token || !authData.expiry) {\n            return false;\n        }\n        \n        // Check if token is expired (with 5 minute buffer)\n        const now = Date.now();\n        const expiryBuffer = 5 * 60 * 1000; // 5 minutes\n        \n        return now < (authData.expiry - expiryBuffer);\n    }\n    \n    /**\n     * Verify token with GitHub API\n     */\n    async verifyToken(token) {\n        const response = await fetch('https://api.github.com/user', {\n            headers: {\n                'Authorization': `Bearer ${token}`,\n                'Accept': 'application/vnd.github.v3+json'\n            }\n        });\n        \n        if (!response.ok) {\n            throw new Error('Token verification failed');\n        }\n        \n        return response.json();\n    }\n    \n    /**\n     * Logout user\n     */\n    logout() {\n        console.log('Logging out...');\n        \n        this.clearAuth();\n        \n        this.notifications.info('Logged out successfully');\n        \n        this.emit('authStateChange', { authenticated: false });\n    }\n    \n    /**\n     * Clear authentication data\n     */\n    clearAuth() {\n        this.authenticated = false;\n        this.user = null;\n        this.permissions = null;\n        \n        localStorage.removeItem('llmxive_auth');\n        sessionStorage.removeItem('oauth_code_verifier');\n        sessionStorage.removeItem('oauth_state');\n    }\n    \n    /**\n     * Clean up URL after OAuth callback\n     */\n    cleanupUrl() {\n        const url = new URL(window.location);\n        url.searchParams.delete('code');\n        url.searchParams.delete('state');\n        url.searchParams.delete('error');\n        window.history.replaceState({}, document.title, url.toString());\n    }\n    \n    /**\n     * Generate PKCE code verifier\n     */\n    generateCodeVerifier() {\n        const array = new Uint8Array(32);\n        crypto.getRandomValues(array);\n        return btoa(String.fromCharCode.apply(null, array))\n            .replace(/\\+/g, '-')\n            .replace(/\\//g, '_')\n            .replace(/=/g, '');\n    }\n    \n    /**\n     * Generate PKCE code challenge\n     */\n    async generateCodeChallenge(verifier) {\n        const encoder = new TextEncoder();\n        const data = encoder.encode(verifier);\n        const digest = await crypto.subtle.digest('SHA-256', data);\n        return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))\n            .replace(/\\+/g, '-')\n            .replace(/\\//g, '_')\n            .replace(/=/g, '');\n    }\n    \n    /**\n     * Generate random state parameter\n     */\n    generateState() {\n        const array = new Uint8Array(16);\n        crypto.getRandomValues(array);\n        return btoa(String.fromCharCode.apply(null, array));\n    }\n    \n    /**\n     * Check if user is authenticated\n     */\n    isAuthenticated() {\n        return this.authenticated;\n    }\n    \n    /**\n     * Get current user\n     */\n    getCurrentUser() {\n        return this.user;\n    }\n    \n    /**\n     * Get user permissions\n     */\n    getUserPermissions() {\n        return this.permissions;\n    }\n    \n    /**\n     * Check if user has write access\n     */\n    canWrite() {\n        return this.permissions && (this.permissions.push || this.permissions.admin);\n    }\n    \n    /**\n     * Check if user is admin\n     */\n    isAdmin() {\n        return this.permissions && this.permissions.admin;\n    }\n    \n    /**\n     * Get authentication headers for API requests\n     */\n    getAuthHeaders() {\n        if (!this.authenticated) {\n            throw new Error('Not authenticated');\n        }\n        \n        const authData = this.getStoredAuth();\n        if (!authData || !this.isTokenValid(authData)) {\n            throw new Error('Invalid or expired token');\n        }\n        \n        return {\n            'Authorization': `Bearer ${authData.token}`,\n            'Accept': 'application/vnd.github.v3+json'\n        };\n    }\n    \n    /**\n     * Refresh authentication if needed\n     */\n    async ensureAuthenticated() {\n        if (!this.authenticated) {\n            throw new Error('Authentication required');\n        }\n        \n        const authData = this.getStoredAuth();\n        if (!authData || !this.isTokenValid(authData)) {\n            // Token is expired, clear auth and require re-login\n            this.clearAuth();\n            this.emit('authStateChange', { \n                authenticated: false, \n                error: 'Session expired' \n            });\n            throw new Error('Session expired, please log in again');\n        }\n        \n        return true;\n    }\n}\n\nexport default AuthManager;