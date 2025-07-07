/**
 * Main Application Controller for llmXive
 * 
 * Initializes the web interface and coordinates between all components
 */

import UnifiedGitHubClient from '../../src/core/UnifiedGitHubClient.js';
import { NotificationManager } from './utils.js';
import { AuthManager } from './auth.js';
import { DashboardManager } from './dashboard.js';
import { ProjectsManager } from './projects.js';
import { ReviewsManager } from './reviews.js';
import { ModelsManager } from './models.js';
import { ModerationManager } from './moderation.js';

class App {
    constructor() {
        this.client = null;
        this.authManager = null;
        this.notifications = null;
        this.currentPage = 'dashboard';
        this.initialized = false;
        
        // Page managers
        this.dashboardManager = null;
        this.projectsManager = null;
        this.reviewsManager = null;
        this.modelsManager = null;
        this.moderationManager = null;
        
        // Bind methods
        this.handlePageNavigation = this.handlePageNavigation.bind(this);
        this.handleAuthStateChange = this.handleAuthStateChange.bind(this);
        this.handleSystemStatusUpdate = this.handleSystemStatusUpdate.bind(this);
        
        // Initialize immediately
        this.initialize();
    }
    
    /**
     * Initialize the application
     */
    async initialize() {
        try {
            console.log('🚀 Initializing llmXive web interface...');
            
            // Show loading screen
            this.showLoadingScreen('Initializing application...');
            
            // Initialize core systems
            await this.initializeCoreServices();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize page managers
            await this.initializePageManagers();
            
            // Try to authenticate
            await this.attemptAuthentication();
            
            // Setup navigation
            this.setupNavigation();
            
            // Update UI state
            this.updateSystemStatus();
            
            // Hide loading screen and show app
            this.hideLoadingScreen();
            
            // Navigate to initial page
            this.navigateToPage(this.getInitialPage());
            
            this.initialized = true;
            console.log('✅ llmXive web interface initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize application:', error);
            this.showCriticalError('Failed to initialize application', error.message);
        }
    }
    
    /**
     * Initialize core services
     */
    async initializeCoreServices() {
        // Initialize GitHub client
        this.client = new UnifiedGitHubClient({
            owner: 'ContextLab',
            repo: 'llmXive',
            branch: 'main'
        });
        
        // Initialize notification system
        this.notifications = new NotificationManager();
        
        // Initialize authentication manager
        this.authManager = new AuthManager(this.client, this.notifications);
        this.authManager.on('authStateChange', this.handleAuthStateChange);
        
        console.log('Core services initialized');
    }
    
    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.initialized) {
                this.refreshData();
            }
        });
        
        // Online/offline status
        window.addEventListener('online', () => {
            this.handleSystemStatusUpdate('online');
            this.notifications.show('Connection restored', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.handleSystemStatusUpdate('offline');
            this.notifications.show('Connection lost', 'warning');
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Unload warning for unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                return 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
        
        console.log('Event listeners set up');
    }
    
    /**
     * Initialize page managers
     */
    async initializePageManagers() {
        this.dashboardManager = new DashboardManager(this.client, this.notifications);
        this.projectsManager = new ProjectsManager(this.client, this.notifications);
        this.reviewsManager = new ReviewsManager(this.client, this.notifications);
        this.modelsManager = new ModelsManager(this.client, this.notifications);
        this.moderationManager = new ModerationManager(this.client, this.notifications);
        
        console.log('Page managers initialized');
    }
    
    /**
     * Attempt authentication
     */
    async attemptAuthentication() {
        try {
            this.showLoadingScreen('Checking authentication...');
            
            const authResult = await this.authManager.initialize();
            
            if (authResult.authenticated) {
                this.showLoadingScreen('Initializing system...');
                
                // Initialize client with authentication
                const clientResult = await this.client.initialize();
                
                if (clientResult.initialized) {
                    console.log('✅ System initialized with authentication');
                    this.handleAuthStateChange({ authenticated: true, user: this.client.getCurrentUser() });
                } else {
                    console.warn('⚠️ Client initialization failed');
                }
            } else {
                console.log('ℹ️ No authentication found');
                this.handleAuthStateChange({ authenticated: false });
            }
            
        } catch (error) {
            console.error('Authentication check failed:', error);
            this.handleAuthStateChange({ authenticated: false, error: error.message });
        }
    }
    
    /**
     * Set up navigation system
     */
    setupNavigation() {
        // Handle navigation clicks
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                if (page) {
                    this.navigateToPage(page);
                }
            });
        });
        
        // Handle back/forward buttons
        window.addEventListener('popstate', (e) => {
            const page = e.state?.page || this.getInitialPage();
            this.navigateToPage(page, false);
        });
        
        console.log('Navigation system set up');
    }
    
    /**
     * Navigate to a specific page
     */
    async navigateToPage(page, pushState = true) {
        if (!this.initialized) {
            console.warn('Cannot navigate before initialization');
            return;
        }
        
        try {
            // Validate page
            const validPages = ['dashboard', 'projects', 'reviews', 'models', 'moderation'];
            if (!validPages.includes(page)) {
                console.warn(`Invalid page: ${page}`);
                page = 'dashboard';
            }
            
            // Check authentication requirements
            if (page !== 'dashboard' && !this.isAuthenticated()) {
                this.notifications.show('Please log in to access this page', 'warning');
                page = 'dashboard';
            }
            
            // Update browser history
            if (pushState) {
                history.pushState({ page }, '', `#${page}`);
            }
            
            // Update navigation state
            this.updateNavigationState(page);
            
            // Show page
            await this.showPage(page);
            
            this.currentPage = page;
            
        } catch (error) {
            console.error(`Failed to navigate to ${page}:`, error);
            this.notifications.show(`Failed to load ${page}`, 'error');
        }
    }
    
    /**
     * Update navigation state
     */
    updateNavigationState(activePage) {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            const isActive = link.dataset.page === activePage;
            link.classList.toggle('active', isActive);
        });
    }
    
    /**
     * Show specific page
     */
    async showPage(page) {
        // Hide all pages
        const pages = document.querySelectorAll('.page');
        pages.forEach(p => p.classList.remove('active'));
        
        // Show target page
        const targetPage = document.getElementById(`page-${page}`);
        if (targetPage) {
            targetPage.classList.add('active');
            
            // Load page content
            await this.loadPageContent(page);
        }
    }
    
    /**
     * Load content for specific page
     */
    async loadPageContent(page) {
        try {
            switch (page) {
                case 'dashboard':
                    await this.dashboardManager.load();
                    break;
                case 'projects':
                    await this.projectsManager.load();
                    break;
                case 'reviews':
                    await this.reviewsManager.load();
                    break;
                case 'models':
                    await this.modelsManager.load();
                    break;
                case 'moderation':
                    await this.moderationManager.load();
                    break;
                default:
                    console.warn(`No loader for page: ${page}`);
            }
        } catch (error) {
            console.error(`Failed to load ${page} content:`, error);
            this.notifications.show(`Failed to load ${page} content`, 'error');
        }
    }
    
    /**
     * Handle authentication state changes
     */
    handleAuthStateChange(authState) {
        const authSection = document.getElementById('auth-section');
        const userMenu = document.getElementById('user-menu');
        
        if (authState.authenticated && authState.user) {
            // Show user menu
            authSection.innerHTML = `
                <div class="user-profile">
                    <img src="${authState.user.avatar_url}" alt="${authState.user.login}" class="user-avatar">
                    <div class="user-info">
                        <span class="user-name">${authState.user.name || authState.user.login}</span>
                        <span class="user-role">Researcher</span>
                    </div>
                    <button class="user-menu-btn" id="user-menu-btn">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <div class="user-dropdown" id="user-dropdown">
                    <a href="#" class="dropdown-item" id="profile-link">
                        <i class="fas fa-user"></i>
                        Profile
                    </a>
                    <a href="#" class="dropdown-item" id="settings-link">
                        <i class="fas fa-cog"></i>
                        Settings
                    </a>
                    <div class="dropdown-divider"></div>
                    <button class="dropdown-item" id="logout-btn">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </button>
                </div>
            `;
            
            // Set up user menu interactions
            this.setupUserMenu();
            
            // Update system status
            this.handleSystemStatusUpdate('authenticated');
            
            // Enable navigation
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('disabled'));
            
        } else {
            // Show login button
            authSection.innerHTML = `
                <button class="btn btn-primary" id="login-btn">
                    <i class="fab fa-github"></i>
                    Login with GitHub
                </button>
            `;
            
            // Set up login handler
            const loginBtn = document.getElementById('login-btn');
            loginBtn.addEventListener('click', () => {
                this.authManager.startAuthFlow();
            });
            
            // Update system status
            this.handleSystemStatusUpdate('unauthenticated');
            
            // Disable navigation except dashboard
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                if (link.dataset.page !== 'dashboard') {
                    link.classList.add('disabled');
                }
            });
        }
        
        // Refresh current page
        if (this.initialized) {
            this.loadPageContent(this.currentPage);
        }
    }
    
    /**
     * Set up user menu interactions
     */
    setupUserMenu() {
        const userMenuBtn = document.getElementById('user-menu-btn');
        const userDropdown = document.getElementById('user-dropdown');
        const logoutBtn = document.getElementById('logout-btn');
        
        if (userMenuBtn && userDropdown) {
            userMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                userDropdown.classList.toggle('active');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                userDropdown.classList.remove('active');
            });
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.authManager.logout();
            });
        }
    }
    
    /**
     * Handle system status updates
     */
    handleSystemStatusUpdate(status) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusDot = statusIndicator?.querySelector('.status-dot');
        const statusText = statusIndicator?.querySelector('.status-text');
        
        if (!statusIndicator) return;
        
        // Remove existing status classes
        statusIndicator.className = 'status-indicator';
        
        switch (status) {
            case 'online':
            case 'authenticated':
                statusIndicator.classList.add('status-online');
                if (statusText) statusText.textContent = 'Online';
                break;
            case 'offline':
                statusIndicator.classList.add('status-offline');
                if (statusText) statusText.textContent = 'Offline';
                break;
            case 'unauthenticated':
                statusIndicator.classList.add('status-warning');
                if (statusText) statusText.textContent = 'Not Authenticated';
                break;
            case 'error':
                statusIndicator.classList.add('status-error');
                if (statusText) statusText.textContent = 'Error';
                break;
            default:
                statusIndicator.classList.add('status-warning');
                if (statusText) statusText.textContent = 'Unknown';
        }
    }
    
    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Only handle shortcuts when not typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case '1':
                    e.preventDefault();
                    this.navigateToPage('dashboard');
                    break;
                case '2':
                    e.preventDefault();
                    this.navigateToPage('projects');
                    break;
                case '3':
                    e.preventDefault();
                    this.navigateToPage('reviews');
                    break;
                case '4':
                    e.preventDefault();
                    this.navigateToPage('models');
                    break;
                case '5':
                    e.preventDefault();
                    this.navigateToPage('moderation');
                    break;
                case 'k':
                    e.preventDefault();
                    this.openCommandPalette();
                    break;
            }
        }
        
        if (e.key === 'Escape') {
            this.closeModals();
        }
    }
    
    /**
     * Get initial page from URL hash or default
     */
    getInitialPage() {
        const hash = window.location.hash.replace('#', '');
        const validPages = ['dashboard', 'projects', 'reviews', 'models', 'moderation'];
        return validPages.includes(hash) ? hash : 'dashboard';
    }
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.authManager?.isAuthenticated() || false;
    }
    
    /**
     * Check if there are unsaved changes
     */
    hasUnsavedChanges() {
        // Check all page managers for unsaved changes
        return [
            this.projectsManager,
            this.reviewsManager,
            this.modelsManager,
            this.moderationManager
        ].some(manager => manager?.hasUnsavedChanges?.() || false);
    }
    
    /**
     * Refresh data for current page
     */
    async refreshData() {
        if (this.initialized) {
            await this.loadPageContent(this.currentPage);
        }
    }
    
    /**
     * Open command palette
     */
    openCommandPalette() {
        // TODO: Implement command palette
        this.notifications.show('Command palette coming soon!', 'info');
    }
    
    /**
     * Close all modals
     */
    closeModals() {
        const modals = document.querySelectorAll('.modal.active');
        modals.forEach(modal => modal.classList.remove('active'));
        
        const overlay = document.getElementById('modal-overlay');
        if (overlay) overlay.classList.remove('active');
    }
    
    /**
     * Show loading screen
     */
    showLoadingScreen(message = 'Loading...') {
        const loadingScreen = document.getElementById('loading-screen');
        const loadingText = loadingScreen?.querySelector('.loading-text p');
        
        if (loadingScreen) {
            loadingScreen.style.display = 'flex';
            if (loadingText) loadingText.textContent = message;
        }
        
        const app = document.getElementById('app');
        if (app) app.style.display = 'none';
    }
    
    /**
     * Hide loading screen
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        const app = document.getElementById('app');
        
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
        
        if (app) {
            app.style.display = 'block';
        }
    }
    
    /**
     * Show critical error
     */
    showCriticalError(title, message) {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.innerHTML = `
                <div class="error-screen">
                    <div class="error-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h2>${title}</h2>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        Reload Application
                    </button>
                </div>
            `;
        }
    }
    
    /**
     * Update system status display
     */
    async updateSystemStatus() {
        try {
            if (this.client && this.isAuthenticated()) {
                const status = await this.client.getSystemStatus();
                
                if (status) {
                    this.handleSystemStatusUpdate('online');
                } else {
                    this.handleSystemStatusUpdate('error');
                }
            }
        } catch (error) {
            console.error('Failed to update system status:', error);
            this.handleSystemStatusUpdate('error');
        }
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.llmXiveApp = new App();
});

// Handle OAuth callback
if (window.location.search.includes('code=')) {
    // OAuth callback detected - the AuthManager will handle this
    console.log('OAuth callback detected');
}

export default App;