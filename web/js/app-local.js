/**
 * Main Application Controller for llmXive (Local Development Version)
 * 
 * Initializes the web interface with better error handling for local development
 */

import { NotificationManager } from './utils.js';
import { DashboardManager } from './dashboard.js';
import { ProjectsManager } from './projects.js';
import { ReviewsManager } from './reviews.js';
import { ModelsManager } from './models.js';
import { ModerationManager } from './moderation.js';

class App {
    constructor() {
        this.client = null; // Will be null in local mode
        this.authManager = null;
        this.notifications = null;
        this.currentPage = 'dashboard';
        this.initialized = false;
        this.isLocalMode = true; // Flag for local development
        
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
            console.log('🚀 Initializing llmXive web interface (Local Mode)...');
            
            // Show loading screen
            this.showLoadingScreen('Initializing application...');
            
            // Initialize core systems (without GitHub client)
            await this.initializeCoreServices();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize page managers
            await this.initializePageManagers();
            
            // Skip authentication in local mode
            this.handleAuthStateChange({ authenticated: false, localMode: true });
            
            // Setup navigation
            this.setupNavigation();
            
            // Update UI state
            this.updateSystemStatus();
            
            // Hide loading screen and show app
            this.hideLoadingScreen();
            
            // Navigate to initial page
            this.navigateToPage(this.getInitialPage());
            
            this.initialized = true;
            console.log('✅ llmXive web interface initialized successfully (Local Mode)');
            
        } catch (error) {
            console.error('❌ Failed to initialize application:', error);
            this.showCriticalError('Failed to initialize application', error.message);
        }
    }
    
    /**
     * Initialize core services (local mode)
     */
    async initializeCoreServices() {
        // Initialize notification system
        this.notifications = new NotificationManager();
        
        // Skip GitHub client and auth manager in local mode
        console.log('Core services initialized (Local Mode)');
        
        // Show local mode notification
        setTimeout(() => {
            this.notifications.show('Running in Local Development Mode - Using mock data', 'info', 5000);
        }, 1000);
    }
    
    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.initialized) {
                console.log('Page visible - would refresh data in production mode');
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        console.log('Event listeners set up (Local Mode)');
    }
    
    /**
     * Initialize page managers (with mock client)
     */
    async initializePageManagers() {
        // Create a mock client for local development
        const mockClient = {
            isAuthenticated: () => false,
            getCurrentUser: () => null,
            getSystemStatus: () => Promise.resolve(true)
        };
        
        this.dashboardManager = new DashboardManager(mockClient, this.notifications);
        this.projectsManager = new ProjectsManager(mockClient, this.notifications);
        this.reviewsManager = new ReviewsManager(mockClient, this.notifications);
        this.modelsManager = new ModelsManager(mockClient, this.notifications);
        this.moderationManager = new ModerationManager(mockClient, this.notifications);
        
        console.log('Page managers initialized (Local Mode)');
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
     * Handle authentication state changes (local mode)
     */
    handleAuthStateChange(authState) {
        const authSection = document.getElementById('auth-section');
        
        if (authState.localMode) {
            // Show local mode indicator
            authSection.innerHTML = `
                <div class="local-mode-indicator">
                    <i class="fas fa-laptop-code"></i>
                    <span>Local Development Mode</span>
                </div>
            `;
            
            // Update system status
            this.handleSystemStatusUpdate('local');
            
        } else {
            // Show login button (for future production mode)
            authSection.innerHTML = `
                <button class="btn btn-primary" id="login-btn">
                    <i class="fab fa-github"></i>
                    Login with GitHub
                </button>
            `;
        }
        
        // Refresh current page
        if (this.initialized) {
            this.loadPageContent(this.currentPage);
        }
    }
    
    /**
     * Handle system status updates
     */
    handleSystemStatusUpdate(status) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = statusIndicator?.querySelector('.status-text');
        
        if (!statusIndicator) return;
        
        // Remove existing status classes
        statusIndicator.className = 'status-indicator';
        
        switch (status) {
            case 'local':
                statusIndicator.classList.add('status-warning');
                if (statusText) statusText.textContent = 'Local Mode';
                break;
            case 'online':
                statusIndicator.classList.add('status-online');
                if (statusText) statusText.textContent = 'Online';
                break;
            case 'offline':
                statusIndicator.classList.add('status-offline');
                if (statusText) statusText.textContent = 'Offline';
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
            }
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
        // In local mode, just set to local status
        this.handleSystemStatusUpdate('local');
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.llmXiveApp = new App();
});

export default App;