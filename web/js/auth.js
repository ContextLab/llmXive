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
            
            // Store PKCE parameters securely
            sessionStorage.setItem('oauth_code_verifier', codeVerifier);
            sessionStorage.setItem('oauth_state', state);
            
            // Build authorization URL with environment-specific client ID
            const clientId = this.getClientId();
            const redirectUri = window.location.origin + window.location.pathname;
            const scope = 'repo read:user';
            
            const authUrl = new URL('https://github.com/login/oauth/authorize');
            authUrl.searchParams.set('client_id', clientId);
            authUrl.searchParams.set('redirect_uri', redirectUri);
            authUrl.searchParams.set('scope', scope);
            authUrl.searchParams.set('state', state);
            authUrl.searchParams.set('code_challenge', codeChallenge);
            authUrl.searchParams.set('code_challenge_method', 'S256');
            
            console.log('Redirecting to GitHub for authentication...');
            window.location.href = authUrl.toString();
            
        } catch (error) {
            console.error('Failed to start OAuth flow:', error);
            this.notifications.error('Failed to start authentication');
        }
    }
    
    /**
     * Handle OAuth callback
     */
    async handleAuthCallback(code, state) {
        try {
            console.log('Handling OAuth callback...');
            
            // Verify state parameter to prevent CSRF
            const storedState = sessionStorage.getItem('oauth_state');
            if (state !== storedState) {
                throw new Error('Invalid state parameter - possible CSRF attack');
            }
            
            // Get code verifier
            const codeVerifier = sessionStorage.getItem('oauth_code_verifier');
            if (!codeVerifier) {
                throw new Error('No code verifier found');
            }
            
            this.notifications.info('Exchanging code for token...');
            
            // Exchange code for token
            const tokenData = await this.exchangeCodeForToken(code, codeVerifier);
            
            // Store authentication data securely
            await this.storeAuth(tokenData);
            
            // Clean up
            sessionStorage.removeItem('oauth_code_verifier');
            sessionStorage.removeItem('oauth_state');
            this.cleanupUrl();
            
            this.notifications.success('Authentication successful!');
            
            // Emit auth state change
            this.emit('authStateChange', {
                authenticated: true,
                user: this.user,
                permissions: this.permissions
            });
            
        } catch (error) {
            console.error('OAuth callback failed:', error);
            this.notifications.error(`Authentication failed: ${error.message}`);
            
            // Clean up on error
            sessionStorage.removeItem('oauth_code_verifier');
            sessionStorage.removeItem('oauth_state');
            this.cleanupUrl();
            
            this.emit('authStateChange', { 
                authenticated: false, 
                error: error.message 
            });
        }
    }
    
    /**
     * Exchange authorization code for access token
     */
    async exchangeCodeForToken(code, codeVerifier) {
        // Use existing Heroku proxy with error handling
        const proxyUrl = 'https://llmxive-auth-b300c94fab60.herokuapp.com/authenticate/';
        
        try {
            const response = await fetch(proxyUrl + encodeURIComponent(code), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'User-Agent': 'llmXive/1.0'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(`OAuth error: ${data.error}`);
            }
            
            return {
                access_token: data.token || data.access_token,
                token_type: data.token_type || 'bearer',
                expires_in: data.expires_in || 3600, // Default 1 hour
                scope: data.scope
            };
            
        } catch (error) {
            console.error('Token exchange failed:', error);
            throw new Error(`Failed to exchange code for token: ${error.message}`);
        }
    }
    
    /**
     * Store authentication data with enhanced security
     */
    async storeAuth(tokenData) {
        const token = tokenData.access_token;
        const tokenExpiry = Date.now() + (tokenData.expires_in * 1000);
        
        try {
            // Get user information
            const userResponse = await fetch('https://api.github.com/user', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'llmXive/1.0'
                }
            });
            
            if (!userResponse.ok) {
                throw new Error('Failed to fetch user information');
            }
            
            const user = await userResponse.json();
            
            // Get repository permissions
            let permissions = null;
            try {
                const permsResponse = await fetch('https://api.github.com/repos/ContextLab/llmXive', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'llmXive/1.0'
                    }
                });
                
                if (permsResponse.ok) {
                    const repoData = await permsResponse.json();
                    permissions = repoData.permissions;
                }
            } catch (error) {
                console.warn('Failed to fetch repository permissions:', error);
            }
            
            // Update instance state
            this.authenticated = true;
            this.user = user;
            this.permissions = permissions;
            
            // Store with basic obfuscation in sessionStorage for security
            const authData = {
                token,
                user,
                permissions,
                expiry: tokenExpiry,
                stored: Date.now()
            };
            
            // Basic obfuscation (not encryption, but better than plain text)
            const obfuscated = btoa(JSON.stringify(authData));
            sessionStorage.setItem('llmxive_auth_secure', obfuscated);
            
            // Remove any legacy localStorage data
            localStorage.removeItem('llmxive_auth');
            
            console.log('Authentication data stored securely');
            
        } catch (error) {
            console.error('Failed to store auth data:', error);
            throw error;
        }
    }
    
    /**
     * Get stored authentication data with fallback to legacy
     */
    getStoredAuth() {
        try {
            // Try secure storage first
            const obfuscated = sessionStorage.getItem('llmxive_auth_secure');
            if (obfuscated) {
                return JSON.parse(atob(obfuscated));
            }
            
            // Fallback to legacy storage and migrate
            const legacy = localStorage.getItem('llmxive_auth');
            if (legacy) {
                const authData = JSON.parse(legacy);
                // Migrate to secure storage
                const obfuscated = btoa(JSON.stringify(authData));
                sessionStorage.setItem('llmxive_auth_secure', obfuscated);
                localStorage.removeItem('llmxive_auth');
                return authData;
            }
            
            return null;
        } catch (error) {
            console.error('Error reading stored auth:', error);
            return null;
        }
    }
    
    /**
     * Check if token is valid
     */
    isTokenValid(authData) {
        if (!authData || !authData.token || !authData.expiry) {
            return false;
        }
        
        // Check if token is expired (with 5 minute buffer)
        const now = Date.now();
        const expiryBuffer = 5 * 60 * 1000; // 5 minutes
        
        return now < (authData.expiry - expiryBuffer);
    }
    
    /**
     * Verify token with GitHub API
     */
    async verifyToken(token) {
        const response = await fetch('https://api.github.com/user', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'llmXive/1.0'
            }
        });
        
        if (!response.ok) {
            throw new Error('Token verification failed');
        }
        
        return response.json();
    }
    
    /**
     * Logout user
     */
    logout() {
        console.log('Logging out...');
        
        this.clearAuth();
        
        this.notifications.info('Logged out successfully');
        
        this.emit('authStateChange', { authenticated: false });
    }
    
    /**
     * Clear authentication data securely
     */
    clearAuth() {
        this.authenticated = false;
        this.user = null;
        this.permissions = null;
        
        // Clear both secure and legacy storage
        sessionStorage.removeItem('llmxive_auth_secure');
        localStorage.removeItem('llmxive_auth');
        sessionStorage.removeItem('oauth_code_verifier');
        sessionStorage.removeItem('oauth_state');
    }
    
    /**
     * Clean up URL after OAuth callback
     */
    cleanupUrl() {
        const url = new URL(window.location);
        url.searchParams.delete('code');
        url.searchParams.delete('state');
        url.searchParams.delete('error');
        window.history.replaceState({}, document.title, url.toString());
    }
    
    /**
     * Generate PKCE code verifier
     */
    generateCodeVerifier() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array))
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=/g, '');
    }
    
    /**
     * Generate PKCE code challenge
     */
    async generateCodeChallenge(verifier) {
        const encoder = new TextEncoder();
        const data = encoder.encode(verifier);
        const digest = await crypto.subtle.digest('SHA-256', data);
        return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=/g, '');
    }
    
    /**
     * Generate random state parameter
     */
    generateState() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array));
    }
    
    /**
     * Get client ID from environment or fallback
     */
    getClientId() {
        // Try environment variable first (for build-time injection)
        if (typeof process !== 'undefined' && process.env && process.env.GITHUB_CLIENT_ID) {
            return process.env.GITHUB_CLIENT_ID;
        }
        
        // Try window global (for runtime injection)
        if (window.LLMXIVE_CONFIG && window.LLMXIVE_CONFIG.GITHUB_CLIENT_ID) {
            return window.LLMXIVE_CONFIG.GITHUB_CLIENT_ID;
        }
        
        // Fallback to existing client ID (for development)
        return 'Ov23liY5hzeo5JVmlzcH';
    }
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.authenticated;
    }
    
    /**
     * Get current user
     */
    getCurrentUser() {
        return this.user;
    }
    
    /**
     * Get user permissions
     */
    getUserPermissions() {
        return this.permissions;
    }
    
    /**
     * Check if user has write access
     */
    canWrite() {
        return this.permissions && (this.permissions.push || this.permissions.admin);
    }
    
    /**
     * Check if user is admin
     */
    isAdmin() {
        return this.permissions && this.permissions.admin;
    }
    
    /**
     * Get authentication headers for API requests
     */
    getAuthHeaders() {
        if (!this.authenticated) {
            throw new Error('Not authenticated');
        }
        
        const authData = this.getStoredAuth();
        if (!authData || !this.isTokenValid(authData)) {
            throw new Error('Invalid or expired token');
        }
        
        return {
            'Authorization': `Bearer ${authData.token}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'llmXive/1.0'
        };
    }
    
    /**
     * Refresh authentication if needed
     */
    async ensureAuthenticated() {
        if (!this.authenticated) {
            throw new Error('Authentication required');
        }
        
        const authData = this.getStoredAuth();
        if (!authData || !this.isTokenValid(authData)) {
            // Token is expired, clear auth and require re-login
            this.clearAuth();
            this.emit('authStateChange', { 
                authenticated: false, 
                error: 'Session expired' 
            });
            throw new Error('Session expired, please log in again');
        }
        
        return true;
    }
}

export default AuthManager;