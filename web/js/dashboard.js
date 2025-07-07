/**
 * Dashboard Manager for llmXive
 * Handles dashboard data loading, statistics, and activity feeds
 */

import { EventTarget } from './events.js';
import { DateUtils, NumberUtils, DOMUtils } from './utils.js';

export class DashboardManager extends EventTarget {
    constructor(client, notifications) {
        super();
        
        this.client = client;
        this.notifications = notifications;
        this.refreshInterval = null;
        this.activityUpdateInterval = null;
        this.statisticsCache = null;
        this.lastRefresh = null;
        
        // Bind methods
        this.handleRefreshClick = this.handleRefreshClick.bind(this);
        this.handleQuickAction = this.handleQuickAction.bind(this);
        
        // Auto-refresh interval (5 minutes)
        this.autoRefreshInterval = 5 * 60 * 1000;
    }
    
    /**
     * Load dashboard content
     */
    async load() {
        try {
            console.log('Loading dashboard...');
            
            // Show loading state
            this.showLoadingState();
            
            // Load statistics and activity in parallel
            await Promise.all([
                this.loadStatistics(),
                this.loadRecentActivity()
            ]);
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            this.lastRefresh = new Date();
            console.log('Dashboard loaded successfully');
            
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showErrorState(error.message);
        }
    }
    
    /**
     * Load dashboard statistics
     */
    async loadStatistics() {
        try {
            // Check cache first
            if (this.statisticsCache && this.isCacheValid()) {
                this.displayStatistics(this.statisticsCache);
                return;
            }
            
            console.log('Fetching dashboard statistics...');
            
            // Simulate API calls (replace with actual implementation)
            const stats = await this.fetchStatistics();
            
            this.statisticsCache = stats;
            this.displayStatistics(stats);
            
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.displayStatistics(this.getDefaultStatistics());
        }
    }
    
    /**
     * Fetch statistics from API
     */
    async fetchStatistics() {
        // TODO: Replace with actual API calls
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    totalProjects: Math.floor(Math.random() * 50) + 10,
                    totalReviews: Math.floor(Math.random() * 200) + 50,
                    aiCalls: Math.floor(Math.random() * 1000) + 100,
                    completionRate: Math.floor(Math.random() * 40) + 60
                });
            }, 500);
        });
    }
    
    /**
     * Display statistics on dashboard
     */
    displayStatistics(stats) {
        const elements = {
            totalProjects: document.getElementById('total-projects'),
            totalReviews: document.getElementById('total-reviews'),
            aiCalls: document.getElementById('ai-calls'),
            completionRate: document.getElementById('completion-rate')
        };
        
        // Animate counter updates
        if (elements.totalProjects) {
            this.animateCounter(elements.totalProjects, stats.totalProjects);
        }
        
        if (elements.totalReviews) {
            this.animateCounter(elements.totalReviews, stats.totalReviews);
        }
        
        if (elements.aiCalls) {
            this.animateCounter(elements.aiCalls, stats.aiCalls);
        }
        
        if (elements.completionRate) {
            this.animateCounter(elements.completionRate, stats.completionRate, '%');
        }
    }
    
    /**
     * Animate counter from current value to target
     */
    animateCounter(element, targetValue, suffix = '') {
        const currentValue = parseInt(element.textContent) || 0;
        const increment = Math.ceil((targetValue - currentValue) / 20);
        const duration = 50;
        
        let current = currentValue;
        
        const timer = setInterval(() => {
            current += increment;
            
            if ((increment > 0 && current >= targetValue) || 
                (increment < 0 && current <= targetValue)) {
                current = targetValue;
                clearInterval(timer);
            }
            
            element.textContent = NumberUtils.formatNumber(current) + suffix;
            element.classList.add('counting');
            
            setTimeout(() => {
                element.classList.remove('counting');
            }, duration);
        }, duration);
    }
    
    /**
     * Load recent activity feed
     */
    async loadRecentActivity() {
        try {
            console.log('Loading recent activity...');
            
            const activityFeed = document.getElementById('activity-feed');
            if (!activityFeed) return;
            
            // Show loading
            activityFeed.innerHTML = `
                <div class="activity-item loading">
                    <div class="activity-spinner"></div>
                    <span>Loading recent activity...</span>
                </div>
            `;
            
            // Fetch activity data
            const activities = await this.fetchRecentActivity();
            
            if (activities.length === 0) {
                this.showEmptyActivity();
                return;
            }
            
            // Render activities
            activityFeed.innerHTML = activities.map(activity => 
                this.renderActivityItem(activity)
            ).join('');
            
        } catch (error) {
            console.error('Failed to load activity:', error);
            this.showActivityError();
        }
    }
    
    /**
     * Fetch recent activity from API
     */
    async fetchRecentActivity() {
        // TODO: Replace with actual API calls
        return new Promise(resolve => {
            setTimeout(() => {
                const activities = [
                    {
                        id: '1',
                        type: 'project_created',
                        title: 'New project "AI Safety Research" created',
                        description: 'Automated scientific discovery project focusing on AI alignment',
                        timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
                        user: { name: 'Claude', avatar: null },
                        icon: 'fas fa-plus',
                        iconClass: 'success'
                    },
                    {
                        id: '2',
                        type: 'review_generated',
                        title: 'Automated review completed',
                        description: 'Technical design review for "Neural Network Optimization"',
                        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
                        user: { name: 'GPT-4', avatar: null },
                        icon: 'fas fa-comments',
                        iconClass: ''
                    },
                    {
                        id: '3',
                        type: 'phase_advancement',
                        title: 'Project advanced to implementation phase',
                        description: '"Quantum Computing Applications" met review requirements',
                        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
                        user: { name: 'System', avatar: null },
                        icon: 'fas fa-arrow-up',
                        iconClass: 'warning'
                    }
                ];
                resolve(activities);
            }, 300);
        });
    }
    
    /**
     * Render activity item HTML
     */
    renderActivityItem(activity) {
        const relativeTime = DateUtils.formatRelative(activity.timestamp);
        const avatarHtml = activity.user.avatar ? 
            `<img src="${activity.user.avatar}" alt="${activity.user.name}" class="user-avatar">` :
            `<div class="user-avatar-placeholder">${activity.user.name.charAt(0)}</div>`;
        
        return `
            <div class="activity-item" data-activity-id="${activity.id}">
                <div class="activity-icon ${activity.iconClass}">
                    <i class="${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-meta">
                        <div class="activity-user">
                            ${avatarHtml}
                            <span>${activity.user.name}</span>
                        </div>
                        <div class="activity-time" title="${DateUtils.formatDateTime(activity.timestamp)}">
                            ${relativeTime}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Show empty activity state
     */
    showEmptyActivity() {
        const activityFeed = document.getElementById('activity-feed');
        if (!activityFeed) return;
        
        activityFeed.innerHTML = `
            <div class="activity-empty">
                <i class="fas fa-history"></i>
                <h3>No Recent Activity</h3>
                <p>Activity will appear here as you work on projects</p>
            </div>
        `;
    }
    
    /**
     * Show activity error state
     */
    showActivityError() {
        const activityFeed = document.getElementById('activity-feed');
        if (!activityFeed) return;
        
        activityFeed.innerHTML = `
            <div class="activity-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Failed to load activity feed</span>
                <button class="btn btn-sm btn-secondary" onclick="this.closest('.activity-section').querySelector('#refresh-activity').click()">
                    Retry
                </button>
            </div>
        `;
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-activity');
        if (refreshBtn) {
            refreshBtn.removeEventListener('click', this.handleRefreshClick);
            refreshBtn.addEventListener('click', this.handleRefreshClick);
        }
        
        // Quick action buttons
        const quickActions = [
            'create-project-btn',
            'run-reviews-btn',
            'view-models-btn',
            'system-status-btn'
        ];
        
        quickActions.forEach(actionId => {
            const button = document.getElementById(actionId);
            if (button) {
                button.removeEventListener('click', this.handleQuickAction);
                button.addEventListener('click', this.handleQuickAction);
            }
        });
    }
    
    /**
     * Handle refresh button click
     */
    async handleRefreshClick(event) {
        event.preventDefault();
        
        const button = event.target.closest('button');
        const originalContent = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
        button.disabled = true;
        
        try {
            await Promise.all([
                this.loadStatistics(),
                this.loadRecentActivity()
            ]);
            
            this.notifications.success('Dashboard refreshed successfully');
            
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
            this.notifications.error('Failed to refresh dashboard');
        } finally {
            // Restore button state
            button.innerHTML = originalContent;
            button.disabled = false;
        }
    }
    
    /**
     * Handle quick action button clicks
     */
    handleQuickAction(event) {
        event.preventDefault();
        
        const button = event.target.closest('button');
        const actionId = button.id;
        
        switch (actionId) {
            case 'create-project-btn':
                this.emit('navigate', { page: 'projects', action: 'create' });
                break;
            case 'run-reviews-btn':
                this.runAutomatedReviews();
                break;
            case 'view-models-btn':
                this.emit('navigate', { page: 'models' });
                break;
            case 'system-status-btn':
                this.showSystemStatus();
                break;
        }
    }
    
    /**
     * Run automated reviews
     */
    async runAutomatedReviews() {
        try {
            this.notifications.info('Starting automated review generation...');
            
            // TODO: Implement actual review generation
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            this.notifications.success('Automated reviews completed');
            
            // Refresh activity feed
            await this.loadRecentActivity();
            
        } catch (error) {
            console.error('Failed to run automated reviews:', error);
            this.notifications.error('Failed to run automated reviews');
        }
    }
    
    /**
     * Show system status modal
     */
    showSystemStatus() {
        // TODO: Implement system status modal
        this.notifications.info('System status: All services operational');
    }
    
    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadStatistics();
        }, this.autoRefreshInterval);
        
        // Activity feed updates more frequently
        if (this.activityUpdateInterval) {
            clearInterval(this.activityUpdateInterval);
        }
        
        this.activityUpdateInterval = setInterval(() => {
            this.loadRecentActivity();
        }, 2 * 60 * 1000); // 2 minutes
    }
    
    /**
     * Stop auto-refresh timer
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        if (this.activityUpdateInterval) {
            clearInterval(this.activityUpdateInterval);
            this.activityUpdateInterval = null;
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        // Statistics loading
        const statElements = [
            'total-projects',
            'total-reviews', 
            'ai-calls',
            'completion-rate'
        ];
        
        statElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '...';
                element.classList.add('loading');
            }
        });
    }
    
    /**
     * Show error state
     */
    showErrorState(message) {
        this.notifications.error(`Dashboard error: ${message}`);
        
        // Show error in activity feed
        const activityFeed = document.getElementById('activity-feed');
        if (activityFeed) {
            activityFeed.innerHTML = `
                <div class="activity-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Failed to load dashboard data</span>
                </div>
            `;
        }
    }
    
    /**
     * Check if statistics cache is valid
     */
    isCacheValid() {
        if (!this.lastRefresh) return false;
        
        const cacheTimeout = 2 * 60 * 1000; // 2 minutes
        return Date.now() - this.lastRefresh.getTime() < cacheTimeout;
    }
    
    /**
     * Get default statistics for error states
     */
    getDefaultStatistics() {
        return {
            totalProjects: 0,
            totalReviews: 0,
            aiCalls: 0,
            completionRate: 0
        };
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        this.stopAutoRefresh();
        
        // Remove event listeners
        const refreshBtn = document.getElementById('refresh-activity');
        if (refreshBtn) {
            refreshBtn.removeEventListener('click', this.handleRefreshClick);
        }
        
        // Clear cache
        this.statisticsCache = null;
        this.lastRefresh = null;
        
        console.log('Dashboard manager cleaned up');
    }
}

export default DashboardManager;