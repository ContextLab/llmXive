/**
 * UnifiedGitHubClient - Main client for GitHub-native llmXive
 * 
 * Provides unified interface for all GitHub operations with authentication,
 * file management, and system configuration.
 */

import FileManager from './FileManager.js';
import SystemConfig from './SystemConfig.js';
import ProjectManager from '../managers/ProjectManager.js';
import ReviewManager from '../managers/ReviewManager.js';
import ModelManager from '../managers/ModelManager.js';
import AutomatedReviewManager from '../managers/AutomatedReviewManager.js';
import ModerationManager from '../managers/ModerationManager.js';

class AuthManager {
    constructor() {
        this.token = null;
        this.user = null;
        this.permissions = null;
        this.tokenExpiry = null;
    }
    
    /**
     * Initialize GitHub OAuth authentication
     */
    async initialize() {
        // Check for existing token in localStorage
        const storedAuth = this.getStoredAuth();
        if (storedAuth && this.isTokenValid(storedAuth)) {
            this.token = storedAuth.token;
            this.user = storedAuth.user;
            this.permissions = storedAuth.permissions;
            this.tokenExpiry = storedAuth.expiry;
            return true;
        }
        
        return false;
    }
    
    /**
     * Start OAuth flow
     */
    async startOAuthFlow(options = {}) {
        const clientId = options.clientId || 'Ov23liY5hzeo5JVmlzcH';
        const redirectUri = options.redirectUri || 'https://contextlab.github.io/llmXive/';
        const scope = options.scope || 'repo read:user';
        
        // Generate PKCE parameters
        const codeVerifier = this.generateCodeVerifier();
        const codeChallenge = await this.generateCodeChallenge(codeVerifier);
        const state = this.generateState();
        
        // Store PKCE parameters
        sessionStorage.setItem('oauth_code_verifier', codeVerifier);
        sessionStorage.setItem('oauth_state', state);
        
        // Build authorization URL
        const authUrl = new URL('https://github.com/login/oauth/authorize');
        authUrl.searchParams.set('client_id', clientId);
        authUrl.searchParams.set('redirect_uri', redirectUri);
        authUrl.searchParams.set('scope', scope);
        authUrl.searchParams.set('state', state);
        authUrl.searchParams.set('code_challenge', codeChallenge);
        authUrl.searchParams.set('code_challenge_method', 'S256');
        
        // Redirect to GitHub
        window.location.href = authUrl.toString();
    }
    
    /**
     * Handle OAuth callback
     */
    async handleOAuthCallback(code, state) {
        // Verify state parameter
        const storedState = sessionStorage.getItem('oauth_state');
        if (state !== storedState) {
            throw new Error('Invalid state parameter');
        }
        
        // Get code verifier
        const codeVerifier = sessionStorage.getItem('oauth_code_verifier');
        if (!codeVerifier) {
            throw new Error('No code verifier found');
        }
        
        try {
            // Exchange code for token
            const tokenResponse = await this.exchangeCodeForToken(code, codeVerifier);
            
            // Store authentication
            await this.storeAuth(tokenResponse);
            
            // Clean up session storage
            sessionStorage.removeItem('oauth_code_verifier');
            sessionStorage.removeItem('oauth_state');
            
            return true;
            
        } catch (error) {
            console.error('OAuth callback failed:', error);
            throw error;
        }
    }
    
    /**
     * Exchange authorization code for access token (via existing Heroku proxy)
     */
    async exchangeCodeForToken(code, codeVerifier) {
        // Use existing working Heroku proxy
        const proxyUrl = 'https://llmxive-auth-b300c94fab60.herokuapp.com/authenticate/';
        
        try {
            const response = await fetch(proxyUrl + code);
            
            if (!response.ok) {
                throw new Error('Failed to exchange code for token');
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(`OAuth error: ${data.error}`);
            }
            
            // Return standardized format
            return {
                access_token: data.token || data.access_token,
                token_type: data.token_type || 'bearer',
                expires_in: data.expires_in,
                scope: data.scope
            };
            
        } catch (error) {
            console.error('Token exchange failed:', error);
            throw error;
        }
    }
    
    /**
     * Store authentication data
     */
    async storeAuth(tokenData) {
        this.token = tokenData.access_token;
        this.tokenExpiry = Date.now() + (tokenData.expires_in * 1000);
        
        // Get user information
        const userResponse = await fetch('https://api.github.com/user', {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });
        
        if (userResponse.ok) {
            this.user = await userResponse.json();
        }
        
        // Get repository permissions
        const permsResponse = await fetch('https://api.github.com/repos/ContextLab/llmXive', {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Accept': 'application/vnd.github.v3+json'
            }
        });
        
        if (permsResponse.ok) {
            const repoData = await permsResponse.json();
            this.permissions = repoData.permissions;
        }
        
        // Store in localStorage
        const authData = {
            token: this.token,
            user: this.user,
            permissions: this.permissions,
            expiry: this.tokenExpiry,
            stored: Date.now()
        };
        
        localStorage.setItem('llmxive_auth', JSON.stringify(authData));
    }
    
    /**
     * Get stored authentication data
     */
    getStoredAuth() {
        try {
            const stored = localStorage.getItem('llmxive_auth');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.error('Error reading stored auth:', error);
        }
        return null;
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
     * Clear authentication
     */
    logout() {
        this.token = null;
        this.user = null;
        this.permissions = null;
        this.tokenExpiry = null;
        
        localStorage.removeItem('llmxive_auth');
        sessionStorage.removeItem('oauth_code_verifier');
        sessionStorage.removeItem('oauth_state');
    }
    
    /**
     * Generate PKCE code verifier
     */
    generateCodeVerifier() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array))
            .replace(/\\+/g, '-')
            .replace(/\\//g, '_')
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
            .replace(/\\+/g, '-')
            .replace(/\\//g, '_')
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
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.token !== null && this.isTokenValid({
            token: this.token,
            expiry: this.tokenExpiry
        });
    }
    
    /**
     * Get authentication headers
     */
    getAuthHeaders() {
        if (!this.isAuthenticated()) {
            throw new Error('Not authenticated');
        }
        
        return {
            'Authorization': `Bearer ${this.token}`,
            'Accept': 'application/vnd.github.v3+json'
        };
    }
}

class UnifiedGitHubClient {
    constructor(options = {}) {
        this.options = {
            owner: 'ContextLab',
            repo: 'llmXive',
            branch: 'main',
            ...options
        };
        
        // Initialize components
        this.auth = new AuthManager();
        this.github = null; // Will be initialized after auth
        this.fileManager = null;
        this.systemConfig = null;
        this.projectManager = null;
        this.reviewManager = null;
        this.modelManager = null;
        this.automatedReviewManager = null;
        this.moderationManager = null;
        
        this.initialized = false;
    }
    
    /**
     * Initialize the client
     */
    async initialize() {
        try {
            console.log('Initializing llmXive GitHub client...');
            
            // Initialize authentication
            const authInitialized = await this.auth.initialize();
            
            if (!authInitialized) {
                console.log('Authentication required');
                return { authenticated: false, initialized: false };
            }
            
            // Initialize GitHub API client
            await this.initializeGitHubAPI();
            
            // Initialize file manager
            this.fileManager = new FileManager(this.github, this.options);
            
            // Initialize system configuration
            this.systemConfig = new SystemConfig(this.fileManager);
            
            // Check if system is initialized
            const systemInitialized = await this.systemConfig.isInitialized();
            
            if (!systemInitialized) {
                console.log('System not initialized, running setup...');
                await this.systemConfig.initialize();
            }
            
            // Initialize managers
            this.projectManager = new ProjectManager(this.fileManager, this.systemConfig);
            this.reviewManager = new ReviewManager(this.fileManager, this.systemConfig, this.projectManager);
            this.modelManager = new ModelManager(this.fileManager, this.systemConfig);
            this.automatedReviewManager = new AutomatedReviewManager(
                this.fileManager, 
                this.systemConfig, 
                this.projectManager, 
                this.reviewManager, 
                this.modelManager
            );
            this.moderationManager = new ModerationManager(
                this.fileManager,
                this.systemConfig,
                this.modelManager
            );
            
            // Initialize model manager
            await this.modelManager.initialize();
            
            this.initialized = true;
            console.log('llmXive client initialized successfully');
            
            return { authenticated: true, initialized: true };
            
        } catch (error) {
            console.error('Failed to initialize client:', error);
            throw error;
        }
    }
    
    /**
     * Initialize GitHub API client (using Octokit or similar)
     */
    async initializeGitHubAPI() {
        // This would typically use @octokit/rest in a real implementation
        // For now, we'll create a simple wrapper around fetch
        
        this.github = {
            rest: {
                repos: {
                    getContent: async (params) => {
                        const url = `https://api.github.com/repos/${params.owner}/${params.repo}/contents/${params.path}`;
                        const queryParams = new URLSearchParams();
                        if (params.ref) queryParams.set('ref', params.ref);
                        
                        const response = await fetch(`${url}?${queryParams}`, {
                            headers: this.auth.getAuthHeaders()
                        });
                        
                        if (!response.ok) {
                            const error = new Error(`GitHub API error: ${response.status}`);
                            error.status = response.status;
                            throw error;
                        }
                        
                        return { data: await response.json() };
                    },
                    
                    createOrUpdateFileContents: async (params) => {
                        const url = `https://api.github.com/repos/${params.owner}/${params.repo}/contents/${params.path}`;
                        
                        const body = {
                            message: params.message,
                            content: params.content,
                            branch: params.branch
                        };
                        
                        if (params.sha) {
                            body.sha = params.sha;
                        }
                        
                        const response = await fetch(url, {
                            method: 'PUT',
                            headers: {
                                ...this.auth.getAuthHeaders(),
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(body)
                        });
                        
                        if (!response.ok) {
                            const error = new Error(`GitHub API error: ${response.status}`);
                            error.status = response.status;
                            throw error;
                        }
                        
                        return { data: await response.json() };
                    }
                }
            }
        };
    }
    
    /**
     * Start authentication flow
     */
    async authenticate(options = {}) {
        try {
            await this.auth.startOAuthFlow(options);
        } catch (error) {
            console.error('Authentication failed:', error);
            throw error;
        }
    }
    
    /**
     * Handle authentication callback
     */
    async handleAuthCallback(code, state) {
        try {
            await this.auth.handleOAuthCallback(code, state);
            
            // Re-initialize after authentication
            return await this.initialize();
            
        } catch (error) {
            console.error('Auth callback failed:', error);
            throw error;
        }
    }
    
    /**
     * Logout user
     */
    logout() {
        this.auth.logout();
        this.github = null;
        this.fileManager = null;
        this.systemConfig = null;
        this.initialized = false;
    }
    
    /**
     * Check if client is ready for use
     */
    isReady() {
        return this.initialized && this.auth.isAuthenticated();
    }
    
    /**
     * Get system status
     */
    async getSystemStatus() {
        if (!this.isReady()) {
            throw new Error('Client not ready');
        }
        
        return await this.systemConfig.getStatus();
    }
    
    /**
     * Load system configuration
     */
    async loadSystemConfig() {
        if (!this.isReady()) {
            throw new Error('Client not ready');
        }
        
        return await this.systemConfig.loadConfig();
    }
    
    /**
     * Load registry data
     */
    async loadRegistries() {
        if (!this.isReady()) {
            throw new Error('Client not ready');
        }
        
        return await this.systemConfig.loadRegistries();
    }
    
    /**
     * Get current user info
     */
    getCurrentUser() {
        return this.auth.user;
    }
    
    /**
     * Get user permissions
     */
    getUserPermissions() {
        return this.auth.permissions;
    }
    
    /**
     * Check if user has write access
     */
    canWrite() {
        return this.auth.permissions && (this.auth.permissions.push || this.auth.permissions.admin);
    }
    
    /**
     * Check if user is admin
     */
    isAdmin() {
        return this.auth.permissions && this.auth.permissions.admin;
    }
}

export default UnifiedGitHubClient;