/**
 * Models Manager for llmXive
 * Handles AI model management, configuration, and monitoring
 */

import { EventTarget } from './events.js';
import { DateUtils, NumberUtils, StringUtils, DOMUtils } from './utils.js';

export class ModelsManager extends EventTarget {
    constructor(client, notifications) {
        super();
        
        this.client = client;
        this.notifications = notifications;
        this.models = [];
        this.providers = [];
        this.usage = [];
        this.filteredModels = [];
        this.currentFilters = {
            provider: '',
            status: '',
            capability: '',
            search: ''
        };
        this.selectedModel = null;
        this.refreshInterval = null;
        
        // Bind methods
        this.handleFilterChange = this.handleFilterChange.bind(this);
        this.handleSearchInput = this.handleSearchInput.bind(this);
        this.handleModelClick = this.handleModelClick.bind(this);
        this.handleModelAction = this.handleModelAction.bind(this);
        this.handleTestModel = this.handleTestModel.bind(this);
        this.handleRefresh = this.handleRefresh.bind(this);
        
        // Debounced search
        this.debouncedSearch = DOMUtils.debounce(this.performSearch.bind(this), 300);
    }
    
    /**
     * Load models page
     */
    async load() {
        try {
            console.log('Loading models...');
            
            // Show loading state
            this.showLoadingState();
            
            // Load data in parallel
            await Promise.all([
                this.loadModels(),
                this.loadProviders(),
                this.loadUsageStatistics()
            ]);
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Apply initial filters
            this.applyFilters();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            console.log('Models page loaded successfully');
            
        } catch (error) {
            console.error('Failed to load models:', error);
            this.showErrorState(error.message);
        }
    }
    
    /**
     * Load models from API
     */
    async loadModels() {
        try {
            console.log('Fetching models...');
            
            // TODO: Replace with actual API call
            this.models = await this.fetchModels();
            this.filteredModels = [...this.models];
            
            this.renderModels();
            this.updateModelStats();
            
        } catch (error) {
            console.error('Failed to fetch models:', error);
            throw error;
        }
    }
    
    /**
     * Load providers from API
     */
    async loadProviders() {
        try {
            console.log('Fetching providers...');
            
            // TODO: Replace with actual API call
            this.providers = await this.fetchProviders();
            
            this.renderProviderStats();
            
        } catch (error) {
            console.error('Failed to fetch providers:', error);
            throw error;
        }
    }
    
    /**
     * Load usage statistics
     */
    async loadUsageStatistics() {
        try {
            console.log('Fetching usage statistics...');
            
            // TODO: Replace with actual API call
            this.usage = await this.fetchUsageStatistics();
            
            this.renderUsageChart();
            
        } catch (error) {
            console.error('Failed to fetch usage statistics:', error);
            throw error;
        }
    }
    
    /**
     * Fetch models from API (mock implementation)
     */
    async fetchModels() {
        // TODO: Replace with actual API calls
        return new Promise(resolve => {
            setTimeout(() => {
                const mockModels = [
                    {
                        id: 'claude-3-sonnet',
                        name: 'Claude 3 Sonnet',
                        provider: 'anthropic',
                        status: 'active',
                        capabilities: ['text', 'reasoning', 'code'],
                        contextWindow: 200000,
                        costPer1kTokens: 0.003,
                        averageLatency: 1200,
                        successRate: 99.2,
                        totalCalls: 1247,
                        totalTokens: 892456,
                        totalCost: 2.68,
                        lastUsed: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
                        configuration: {
                            temperature: 0.7,
                            maxTokens: 4000,
                            topP: 0.9
                        },
                        tags: ['general', 'reasoning', 'analysis']
                    },
                    {
                        id: 'gpt-4-turbo',
                        name: 'GPT-4 Turbo',
                        provider: 'openai',
                        status: 'active',
                        capabilities: ['text', 'reasoning', 'code', 'vision'],
                        contextWindow: 128000,
                        costPer1kTokens: 0.01,
                        averageLatency: 2100,
                        successRate: 98.7,
                        totalCalls: 856,
                        totalTokens: 634521,
                        totalCost: 6.35,
                        lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
                        configuration: {
                            temperature: 0.3,
                            maxTokens: 3000,
                            topP: 0.8
                        },
                        tags: ['general', 'vision', 'coding']
                    },
                    {
                        id: 'gemini-pro',
                        name: 'Gemini Pro',
                        provider: 'google',
                        status: 'rate_limited',
                        capabilities: ['text', 'reasoning', 'multimodal'],
                        contextWindow: 2097152,
                        costPer1kTokens: 0.0005,
                        averageLatency: 1800,
                        successRate: 97.3,
                        totalCalls: 423,
                        totalTokens: 278945,
                        totalCost: 0.14,
                        lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
                        configuration: {
                            temperature: 0.5,
                            maxTokens: 2000,
                            topP: 0.9
                        },
                        tags: ['multimodal', 'large-context', 'cost-effective']
                    },
                    {
                        id: 'claude-3-haiku',
                        name: 'Claude 3 Haiku',
                        provider: 'anthropic',
                        status: 'inactive',
                        capabilities: ['text', 'speed'],
                        contextWindow: 200000,
                        costPer1kTokens: 0.00025,
                        averageLatency: 450,
                        successRate: 99.8,
                        totalCalls: 2156,
                        totalTokens: 456789,
                        totalCost: 0.11,
                        lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
                        configuration: {
                            temperature: 0.8,
                            maxTokens: 1000,
                            topP: 0.95
                        },
                        tags: ['fast', 'cost-effective', 'simple-tasks']
                    }
                ];
                resolve(mockModels);
            }, 700);
        });
    }
    
    /**
     * Fetch providers from API (mock implementation)
     */
    async fetchProviders() {
        return new Promise(resolve => {
            setTimeout(() => {
                const mockProviders = [
                    {
                        id: 'anthropic',
                        name: 'Anthropic',
                        status: 'operational',
                        apiHealth: 99.5,
                        modelCount: 2,
                        totalCalls: 3403,
                        totalCost: 2.79,
                        lastChecked: new Date()
                    },
                    {
                        id: 'openai',
                        name: 'OpenAI',
                        status: 'operational',
                        apiHealth: 98.2,
                        modelCount: 1,
                        totalCalls: 856,
                        totalCost: 6.35,
                        lastChecked: new Date()
                    },
                    {
                        id: 'google',
                        name: 'Google AI',
                        status: 'degraded',
                        apiHealth: 94.1,
                        modelCount: 1,
                        totalCalls: 423,
                        totalCost: 0.14,
                        lastChecked: new Date()
                    }
                ];
                resolve(mockProviders);
            }, 400);
        });
    }
    
    /**
     * Fetch usage statistics (mock implementation)
     */
    async fetchUsageStatistics() {
        return new Promise(resolve => {
            setTimeout(() => {
                const now = new Date();
                const mockUsage = Array.from({ length: 24 }, (_, i) => ({
                    hour: new Date(now.getTime() - (23 - i) * 60 * 60 * 1000),
                    calls: Math.floor(Math.random() * 50) + 10,
                    tokens: Math.floor(Math.random() * 10000) + 1000,
                    cost: (Math.random() * 0.5) + 0.1
                }));
                resolve(mockUsage);
            }, 500);
        });
    }
    
    /**
     * Render models grid
     */
    renderModels() {
        const modelsGrid = document.getElementById('models-grid');
        if (!modelsGrid) return;
        
        if (this.filteredModels.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const modelsHtml = this.filteredModels.map(model => 
            this.renderModelCard(model)
        ).join('');
        
        modelsGrid.innerHTML = modelsHtml;
        
        // Set up model card listeners
        this.setupModelCardListeners();
    }
    
    /**
     * Render individual model card
     */
    renderModelCard(model) {
        const statusClass = model.status.replace('_', '-');
        const providerIcon = this.getProviderIcon(model.provider);
        const capabilityBadges = model.capabilities.map(cap => 
            `<span class="capability-badge">${StringUtils.capitalize(cap)}</span>`
        ).join('');
        
        return `
            <div class="model-card ${statusClass}" data-model-id="${model.id}">
                <div class="model-header">
                    <div class="model-provider">
                        <i class="${providerIcon}"></i>
                        <span>${StringUtils.capitalize(model.provider)}</span>
                    </div>
                    <div class="model-status status-${statusClass}">
                        ${StringUtils.capitalize(model.status.replace('_', ' '))}
                    </div>
                </div>
                
                <div class="model-content">
                    <h3 class="model-name">${model.name}</h3>
                    
                    <div class="model-capabilities">
                        ${capabilityBadges}
                    </div>
                    
                    <div class="model-specs">
                        <div class="model-spec">
                            <span class="model-spec-label">Context</span>
                            <span class="model-spec-value">${NumberUtils.formatNumber(model.contextWindow)}</span>
                        </div>
                        <div class="model-spec">
                            <span class="model-spec-label">Cost/1K</span>
                            <span class="model-spec-value">$${model.costPer1kTokens.toFixed(4)}</span>
                        </div>
                        <div class="model-spec">
                            <span class="model-spec-label">Latency</span>
                            <span class="model-spec-value">${model.averageLatency}ms</span>
                        </div>
                        <div class="model-spec">
                            <span class="model-spec-label">Success</span>
                            <span class="model-spec-value">${model.successRate}%</span>
                        </div>
                    </div>
                    
                    <div class="model-usage">
                        <div class="model-usage-stat">
                            <span class="model-usage-value">${NumberUtils.formatNumber(model.totalCalls)}</span>
                            <span class="model-usage-label">Calls</span>
                        </div>
                        <div class="model-usage-stat">
                            <span class="model-usage-value">${NumberUtils.formatNumber(model.totalTokens)}</span>
                            <span class="model-usage-label">Tokens</span>
                        </div>
                        <div class="model-usage-stat">
                            <span class="model-usage-value">$${model.totalCost.toFixed(2)}</span>
                            <span class="model-usage-label">Cost</span>
                        </div>
                    </div>
                </div>
                
                <div class="model-footer">
                    <div class="model-last-used">
                        Last used ${DateUtils.formatRelative(model.lastUsed)}
                    </div>
                    
                    <div class="model-actions">
                        <button class="model-action" data-action="test" title="Test model">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="model-action" data-action="configure" title="Configure model">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="model-action" data-action="more" title="More options">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Get icon for provider
     */
    getProviderIcon(provider) {
        const icons = {
            anthropic: 'fas fa-brain',
            openai: 'fas fa-robot',
            google: 'fab fa-google'
        };
        return icons[provider] || 'fas fa-microchip';
    }
    
    /**
     * Update model statistics
     */
    updateModelStats() {
        const stats = {
            total: this.models.length,
            active: this.models.filter(m => m.status === 'active').length,
            totalCalls: this.models.reduce((sum, m) => sum + m.totalCalls, 0),
            totalCost: this.models.reduce((sum, m) => sum + m.totalCost, 0)
        };
        
        const totalModelsEl = document.getElementById('total-models');
        const activeModelsEl = document.getElementById('active-models');
        const totalCallsEl = document.getElementById('total-calls');
        const totalCostEl = document.getElementById('total-cost');
        
        if (totalModelsEl) totalModelsEl.textContent = stats.total;
        if (activeModelsEl) activeModelsEl.textContent = stats.active;
        if (totalCallsEl) totalCallsEl.textContent = NumberUtils.formatNumber(stats.totalCalls);
        if (totalCostEl) totalCostEl.textContent = `$${stats.totalCost.toFixed(2)}`;
    }
    
    /**
     * Render provider statistics
     */
    renderProviderStats() {
        const providersList = document.getElementById('providers-list');
        if (!providersList) return;
        
        const providersHtml = this.providers.map(provider => `
            <div class="provider-item status-${provider.status}">
                <div class="provider-info">
                    <div class="provider-name">${provider.name}</div>
                    <div class="provider-status">${StringUtils.capitalize(provider.status)}</div>
                </div>
                <div class="provider-stats">
                    <div class="provider-stat">
                        <span class="provider-stat-value">${provider.apiHealth}%</span>
                        <span class="provider-stat-label">Health</span>
                    </div>
                    <div class="provider-stat">
                        <span class="provider-stat-value">${provider.modelCount}</span>
                        <span class="provider-stat-label">Models</span>
                    </div>
                    <div class="provider-stat">
                        <span class="provider-stat-value">$${provider.totalCost.toFixed(2)}</span>
                        <span class="provider-stat-label">Cost</span>
                    </div>
                </div>
            </div>
        `).join('');
        
        providersList.innerHTML = providersHtml;
    }
    
    /**
     * Render usage chart
     */
    renderUsageChart() {
        const usageChart = document.getElementById('usage-chart');
        if (!usageChart) return;
        
        // Simple text-based chart for now
        // TODO: Implement actual chart library
        const maxCalls = Math.max(...this.usage.map(u => u.calls));
        
        const chartHtml = this.usage.map(point => {
            const height = (point.calls / maxCalls) * 100;
            const hour = point.hour.getHours();
            
            return `
                <div class="usage-bar" title="${point.calls} calls at ${hour}:00">
                    <div class="usage-bar-fill" style="height: ${height}%"></div>
                    <div class="usage-bar-label">${hour}</div>
                </div>
            `;
        }).join('');
        
        usageChart.innerHTML = chartHtml;
    }
    
    /**
     * Show empty state when no models match filters
     */
    showEmptyState() {
        const modelsGrid = document.getElementById('models-grid');
        if (!modelsGrid) return;
        
        const hasActiveFilters = Object.values(this.currentFilters).some(filter => filter !== '');
        
        if (hasActiveFilters) {
            modelsGrid.innerHTML = `
                <div class="models-empty">
                    <i class="fas fa-search"></i>
                    <h3>No Models Found</h3>
                    <p>No models match your current filters. Try adjusting your search criteria.</p>
                    <button class="btn btn-secondary" id="clear-filters-btn">
                        Clear Filters
                    </button>
                </div>
            `;
            
            const clearBtn = document.getElementById('clear-filters-btn');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => this.clearFilters());
            }
        } else {
            modelsGrid.innerHTML = `
                <div class="models-empty">
                    <i class="fas fa-microchip"></i>
                    <h3>No Models Configured</h3>
                    <p>Add AI models to start generating automated reviews and analysis.</p>
                    <button class="btn btn-primary" id="add-model-btn">
                        <i class="fas fa-plus"></i>
                        Add Model
                    </button>
                </div>
            `;
            
            const addBtn = document.getElementById('add-model-btn');
            if (addBtn) {
                addBtn.addEventListener('click', () => this.addNewModel());
            }
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        const modelsGrid = document.getElementById('models-grid');
        if (!modelsGrid) return;
        
        const skeletonCards = Array.from({ length: 4 }, (_, i) => `
            <div class="model-skeleton" style="--index: ${i}"></div>
        `).join('');
        
        modelsGrid.innerHTML = skeletonCards;
    }
    
    /**
     * Show error state
     */
    showErrorState(message) {
        const modelsGrid = document.getElementById('models-grid');
        if (!modelsGrid) return;
        
        modelsGrid.innerHTML = `
            <div class="models-empty">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Failed to Load Models</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="window.location.reload()">
                    <i class="fas fa-sync-alt"></i>
                    Retry
                </button>
            </div>
        `;
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Filter controls
        const providerFilter = document.getElementById('provider-filter');
        const statusFilter = document.getElementById('status-filter');
        const capabilityFilter = document.getElementById('capability-filter');
        const searchInput = document.getElementById('model-search');
        const refreshBtn = document.getElementById('refresh-models');
        const testAllBtn = document.getElementById('test-all-models');
        
        [providerFilter, statusFilter, capabilityFilter].forEach(filter => {
            if (filter) {
                filter.removeEventListener('change', this.handleFilterChange);
                filter.addEventListener('change', this.handleFilterChange);
            }
        });
        
        if (searchInput) {
            searchInput.removeEventListener('input', this.handleSearchInput);
            searchInput.addEventListener('input', this.handleSearchInput);
        }
        
        if (refreshBtn) {
            refreshBtn.removeEventListener('click', this.handleRefresh);
            refreshBtn.addEventListener('click', this.handleRefresh);
        }
        
        if (testAllBtn) {
            testAllBtn.removeEventListener('click', this.handleTestModel);
            testAllBtn.addEventListener('click', this.handleTestModel);
        }
    }
    
    /**
     * Set up model card event listeners
     */
    setupModelCardListeners() {
        // Model card clicks
        const modelCards = document.querySelectorAll('.model-card');
        modelCards.forEach(card => {
            card.removeEventListener('click', this.handleModelClick);
            card.addEventListener('click', this.handleModelClick);
        });
        
        // Model action buttons
        const actionButtons = document.querySelectorAll('.model-action');
        actionButtons.forEach(button => {
            button.removeEventListener('click', this.handleModelAction);
            button.addEventListener('click', this.handleModelAction);
        });
    }
    
    /**
     * Handle filter changes
     */
    handleFilterChange(event) {
        const filterType = event.target.id.replace('-filter', '');
        this.currentFilters[filterType] = event.target.value;
        
        this.applyFilters();
    }
    
    /**
     * Handle search input
     */
    handleSearchInput(event) {
        this.currentFilters.search = event.target.value;
        this.debouncedSearch();
    }
    
    /**
     * Perform search
     */
    performSearch() {
        this.applyFilters();
    }
    
    /**
     * Apply current filters to models
     */
    applyFilters() {
        this.filteredModels = this.models.filter(model => {
            // Provider filter
            if (this.currentFilters.provider && model.provider !== this.currentFilters.provider) {
                return false;
            }
            
            // Status filter
            if (this.currentFilters.status && model.status !== this.currentFilters.status) {
                return false;
            }
            
            // Capability filter
            if (this.currentFilters.capability && !model.capabilities.includes(this.currentFilters.capability)) {
                return false;
            }
            
            // Search filter
            if (this.currentFilters.search) {
                const searchLower = this.currentFilters.search.toLowerCase();
                const matchesName = model.name.toLowerCase().includes(searchLower);
                const matchesProvider = model.provider.toLowerCase().includes(searchLower);
                const matchesTags = model.tags.some(tag => tag.toLowerCase().includes(searchLower));
                
                if (!matchesName && !matchesProvider && !matchesTags) {
                    return false;
                }
            }
            
            return true;
        });
        
        this.renderModels();
        this.updateURLFilters();
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.currentFilters = {
            provider: '',
            status: '',
            capability: '',
            search: ''
        };
        
        // Update filter controls
        const providerFilter = document.getElementById('provider-filter');
        const statusFilter = document.getElementById('status-filter');
        const capabilityFilter = document.getElementById('capability-filter');
        const searchInput = document.getElementById('model-search');
        
        if (providerFilter) providerFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        if (capabilityFilter) capabilityFilter.value = '';
        if (searchInput) searchInput.value = '';
        
        this.applyFilters();
    }
    
    /**
     * Handle model card click
     */
    handleModelClick(event) {
        // Don't trigger if clicking on action buttons
        if (event.target.closest('.model-action')) {
            return;
        }
        
        const card = event.target.closest('.model-card');
        const modelId = card.dataset.modelId;
        const model = this.models.find(m => m.id === modelId);
        
        if (model) {
            this.showModelDetails(model);
        }
    }
    
    /**
     * Handle model action buttons
     */
    handleModelAction(event) {
        event.stopPropagation();
        
        const button = event.target.closest('.model-action');
        const action = button.dataset.action;
        const card = button.closest('.model-card');
        const modelId = card.dataset.modelId;
        const model = this.models.find(m => m.id === modelId);
        
        switch (action) {
            case 'test':
                this.testModel(model);
                break;
            case 'configure':
                this.configureModel(model);
                break;
            case 'more':
                this.showModelMenu(model, button);
                break;
        }
    }
    
    /**
     * Handle refresh button
     */
    async handleRefresh(event) {
        event.preventDefault();
        await this.load();
        this.notifications.success('Models refreshed successfully');
    }
    
    /**
     * Handle test model
     */
    async handleTestModel(event) {
        event.preventDefault();
        
        if (event.target.id === 'test-all-models') {
            await this.testAllModels();
        }
    }
    
    /**
     * Show model details modal
     */
    showModelDetails(model) {
        console.log('Showing model details for:', model.name);
        
        // TODO: Implement model details modal
        this.notifications.info(`Model details for "${model.name}" - Coming soon!`);
        
        this.selectedModel = model;
        this.emit('modelSelected', { model });
    }
    
    /**
     * Test individual model
     */
    async testModel(model) {
        try {
            this.notifications.info(`Testing ${model.name}...`);
            
            // TODO: Implement actual model testing
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            this.notifications.success(`${model.name} test completed successfully`);
            
        } catch (error) {
            console.error('Failed to test model:', error);
            this.notifications.error(`Failed to test ${model.name}`);
        }
    }
    
    /**
     * Test all active models
     */
    async testAllModels() {
        const activeModels = this.models.filter(m => m.status === 'active');
        
        if (activeModels.length === 0) {
            this.notifications.warning('No active models to test');
            return;
        }
        
        this.notifications.info(`Testing ${activeModels.length} active models...`);
        
        try {
            // TODO: Implement batch model testing
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            this.notifications.success(`Successfully tested ${activeModels.length} models`);
            
        } catch (error) {
            console.error('Failed to test models:', error);
            this.notifications.error('Failed to test models');
        }
    }
    
    /**
     * Configure model
     */
    configureModel(model) {
        console.log('Configuring model:', model.name);
        
        // TODO: Implement model configuration modal
        this.notifications.info(`Configure ${model.name} - Coming soon!`);
        
        this.emit('modelConfigure', { model });
    }
    
    /**
     * Show model context menu
     */
    showModelMenu(model, button) {
        // TODO: Implement model context menu
        console.log('Show menu for model:', model.name);
    }
    
    /**
     * Add new model
     */
    addNewModel() {
        console.log('Adding new model...');
        
        // TODO: Implement model addition modal
        this.notifications.info('Add new model - Coming soon!');
        
        this.emit('modelAdd');
    }
    
    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadUsageStatistics();
            this.loadProviders();
        }, 5 * 60 * 1000);
    }
    
    /**
     * Stop auto-refresh timer
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    /**
     * Update URL with current filters
     */
    updateURLFilters() {
        const params = new URLSearchParams();
        
        Object.entries(this.currentFilters).forEach(([key, value]) => {
            if (value) {
                params.set(key, value);
            }
        });
        
        const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}${window.location.hash}`;
        window.history.replaceState(null, '', newUrl);
    }
    
    /**
     * Check for unsaved changes
     */
    hasUnsavedChanges() {
        return false; // Models page doesn't have unsaved changes
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        this.stopAutoRefresh();
        
        // Remove event listeners
        const providerFilter = document.getElementById('provider-filter');
        const statusFilter = document.getElementById('status-filter');
        const capabilityFilter = document.getElementById('capability-filter');
        const searchInput = document.getElementById('model-search');
        const refreshBtn = document.getElementById('refresh-models');
        const testAllBtn = document.getElementById('test-all-models');
        
        [providerFilter, statusFilter, capabilityFilter].forEach(filter => {
            if (filter) {
                filter.removeEventListener('change', this.handleFilterChange);
            }
        });
        
        if (searchInput) {
            searchInput.removeEventListener('input', this.handleSearchInput);
        }
        if (refreshBtn) {
            refreshBtn.removeEventListener('click', this.handleRefresh);
        }
        if (testAllBtn) {
            testAllBtn.removeEventListener('click', this.handleTestModel);
        }
        
        // Clear data
        this.models = [];
        this.providers = [];
        this.usage = [];
        this.filteredModels = [];
        this.selectedModel = null;
        
        console.log('Models manager cleaned up');
    }
}

export default ModelsManager;