/**
 * ModelManager - Manages AI model integration and execution
 * 
 * Handles model selection, API calls, and response processing for the
 * llmXive automated review system. Designed for client-side execution
 * with GitHub Actions for server-side model calls.
 * 
 * SECURITY: Model modifications require admin permissions
 */

import AccessControl, { AccessControlError } from '../core/AccessControl.js';

class ModelManager {
    constructor(fileManager, systemConfig, accessControl = null) {
        this.fileManager = fileManager;
        this.systemConfig = systemConfig;
        this.accessControl = accessControl;
        this.modelsPath = '.llmxive-system/registry/models.json';
        this.providersPath = '.llmxive-system/registry/providers.json';
        
        // Cache for loaded configurations
        this.modelsCache = null;
        this.providersCache = null;
        this.lastCacheUpdate = null;
        this.cacheTimeout = 300000; // 5 minutes
        
        // API client instances
        this.apiClients = new Map();
        
        // Rate limiting and error tracking
        this.rateLimits = new Map();
        this.errorCounts = new Map();
        this.maxRetries = 3;
    }
    
    /**
     * Initialize ModelManager and load configurations
     */
    async initialize() {
        try {
            console.log('Initializing ModelManager...');
            
            await this.loadConfigurations();
            await this.initializeApiClients();
            
            console.log('ModelManager initialized successfully');
            return true;
            
        } catch (error) {
            console.error('Failed to initialize ModelManager:', error);
            throw error;
        }
    }
    
    /**
     * Load model and provider configurations
     */
    async loadConfigurations() {
        const now = Date.now();
        
        // Check if cache is still valid
        if (this.modelsCache && this.providersCache && 
            this.lastCacheUpdate && (now - this.lastCacheUpdate) < this.cacheTimeout) {
            return;
        }
        
        try {
            const [models, providers] = await Promise.all([
                this.fileManager.readJSON(this.modelsPath),
                this.fileManager.readJSON(this.providersPath)
            ]);
            
            this.modelsCache = models;
            this.providersCache = providers;
            this.lastCacheUpdate = now;
            
            console.log(`Loaded ${Object.keys(models.models).length} models and ${Object.keys(providers.providers).length} providers`);
            
        } catch (error) {
            console.error('Failed to load model configurations:', error);
            throw error;
        }
    }
    
    /**
     * Initialize API clients for each provider
     */
    async initializeApiClients() {
        if (!this.providersCache) {
            throw new Error('Provider configuration not loaded');
        }
        
        const providers = this.providersCache.providers;
        
        for (const [providerId, provider] of Object.entries(providers)) {
            if (provider.status === 'active') {
                this.apiClients.set(providerId, {
                    id: providerId,
                    name: provider.name,
                    baseUrl: provider.api_base_url,
                    auth: provider.authentication,
                    rateLimits: provider.rate_limits
                });
            }
        }
        
        console.log(`Initialized ${this.apiClients.size} API clients`);
    }
    
    /**
     * Get available models filtered by capabilities
     */
    async getAvailableModels(capabilities = [], includeUnavailable = false) {
        await this.loadConfigurations();
        
        const models = Object.values(this.modelsCache.models);
        
        return models.filter(model => {
            // Filter by availability
            if (!includeUnavailable && !model.available) {
                return false;
            }
            
            // Filter by capabilities
            if (capabilities.length > 0) {
                return capabilities.every(capability => 
                    model.capabilities.includes(capability)
                );
            }
            
            return true;
        }).sort((a, b) => {
            // Sort by quality score descending, then by reliability
            if (a.quality_score !== b.quality_score) {
                return b.quality_score - a.quality_score;
            }
            return b.reliability_score - a.reliability_score;
        });
    }
    
    /**
     * Select best model for a specific task
     */
    async selectModelForTask(taskType, requirements = {}) {
        const capabilities = this.getRequiredCapabilities(taskType);
        const availableModels = await this.getAvailableModels(capabilities);
        
        if (availableModels.length === 0) {
            throw new Error(`No models available for task type: ${taskType}`);
        }
        
        // Apply additional filtering based on requirements
        let filteredModels = availableModels;
        
        if (requirements.contextWindow) {
            filteredModels = filteredModels.filter(model => 
                model.context_window >= requirements.contextWindow
            );
        }
        
        if (requirements.maxCost) {
            filteredModels = filteredModels.filter(model => 
                model.cost_per_1k_tokens.input <= requirements.maxCost
            );
        }
        
        if (requirements.minQuality) {
            filteredModels = filteredModels.filter(model => 
                model.quality_score >= requirements.minQuality
            );
        }
        
        if (filteredModels.length === 0) {
            console.warn('No models meet all requirements, falling back to available models');
            filteredModels = availableModels;
        }
        
        // Select the best model (first in sorted list)
        const selectedModel = filteredModels[0];
        
        console.log(`Selected model ${selectedModel.id} for task ${taskType}`);
        return selectedModel;
    }
    
    /**
     * Get required capabilities for task type
     */
    getRequiredCapabilities(taskType) {
        const capabilityMap = {
            'concept_validation': ['text_generation', 'research'],
            'feasibility_check': ['text_generation', 'research'],
            'technical_review': ['code_analysis', 'text_generation'],
            'code_review': ['code_analysis', 'text_generation'],
            'paper_review': ['text_generation', 'research'],
            'data_review': ['text_generation', 'research'],
            'implementation_review': ['code_analysis', 'text_generation'],
            'comprehensive_review': ['text_generation', 'research', 'code_analysis'],
            'content_moderation': ['text_generation']
        };
        
        return capabilityMap[taskType] || ['text_generation'];
    }
    
    /**
     * Execute model call (designed for GitHub Actions execution)
     */
    async executeModelCall(modelId, prompt, options = {}) {
        try {
            await this.loadConfigurations();
            
            const model = this.modelsCache.models[modelId];
            if (!model) {
                throw new Error(`Model not found: ${modelId}`);
            }
            
            if (!model.available) {
                throw new Error(`Model not available: ${modelId}`);
            }
            
            const provider = this.providersCache.providers[model.provider];
            if (!provider || provider.status !== 'active') {
                throw new Error(`Provider not available: ${model.provider}`);
            }
            
            // Check rate limits
            await this.checkRateLimit(model.provider);
            
            // Prepare request
            const request = await this.prepareRequest(model, prompt, options);
            
            // Execute with retry logic
            const response = await this.executeWithRetry(model, request);
            
            // Update rate limit tracking
            this.updateRateLimit(model.provider);
            
            // Log successful call
            await this.logModelCall(modelId, prompt, response, 'success');
            
            return {
                success: true,
                model: modelId,
                response: response,
                metadata: {
                    provider: model.provider,
                    timestamp: new Date().toISOString(),
                    processingTime: response.processingTime || null,
                    tokensUsed: response.tokensUsed || null,
                    cost: this.calculateCost(model, response.tokensUsed)
                }
            };
            
        } catch (error) {
            console.error(`Model call failed for ${modelId}:`, error);
            
            // Log failed call
            await this.logModelCall(modelId, prompt, null, 'error', error.message);
            
            throw error;
        }
    }
    
    /**
     * Prepare API request based on provider format
     */
    async prepareRequest(model, prompt, options) {
        const provider = model.provider;
        
        switch (provider) {
            case 'anthropic':
                return this.prepareAnthropicRequest(model, prompt, options);
            case 'openai':
                return this.prepareOpenAIRequest(model, prompt, options);
            case 'google':
                return this.prepareGoogleRequest(model, prompt, options);
            default:
                throw new Error(`Unsupported provider: ${provider}`);
        }
    }
    
    /**
     * Prepare Anthropic API request
     */
    prepareAnthropicRequest(model, prompt, options) {
        return {
            model: model.id,
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ],
            max_tokens: options.maxTokens || model.max_tokens,
            temperature: options.temperature || 0.1,
            top_p: options.topP || 0.9
        };
    }
    
    /**
     * Prepare OpenAI API request
     */
    prepareOpenAIRequest(model, prompt, options) {
        return {
            model: model.id,
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ],
            max_tokens: options.maxTokens || model.max_tokens,
            temperature: options.temperature || 0.1,
            top_p: options.topP || 0.9
        };
    }
    
    /**
     * Prepare Google API request
     */
    prepareGoogleRequest(model, prompt, options) {
        return {
            contents: [
                {
                    parts: [
                        {
                            text: prompt
                        }
                    ]
                }
            ],
            generationConfig: {
                maxOutputTokens: options.maxTokens || model.max_tokens,
                temperature: options.temperature || 0.1,
                topP: options.topP || 0.9
            }
        };
    }
    
    /**
     * Execute request with retry logic
     */
    async executeWithRetry(model, request, attempt = 1) {
        try {
            // In GitHub Actions, this would make actual API calls
            // For client-side, we'll prepare the request for Actions to execute
            
            if (typeof process !== 'undefined' && process.env.GITHUB_ACTIONS) {
                // Running in GitHub Actions - make actual API call
                return await this.makeActualApiCall(model, request);
            } else {
                // Running client-side - prepare for Actions execution
                return await this.scheduleForGitHubActions(model, request);
            }
            
        } catch (error) {
            if (attempt < this.maxRetries && this.isRetryableError(error)) {
                const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
                console.log(`Retry attempt ${attempt + 1} after ${delay}ms delay`);
                
                await this.sleep(delay);
                return await this.executeWithRetry(model, request, attempt + 1);
            }
            
            throw error;
        }
    }
    
    /**
     * Make actual API call (for GitHub Actions)
     */
    async makeActualApiCall(model, request) {
        const provider = this.providersCache.providers[model.provider];
        const apiKey = process.env[`${provider.id.toUpperCase()}_API_KEY`];
        
        if (!apiKey) {
            throw new Error(`API key not found for provider: ${provider.id}`);
        }
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(this.getApiEndpoint(provider, model), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthHeader(provider, apiKey),
                    ...this.getProviderHeaders(provider)
                },
                body: JSON.stringify(request)
            });
            
            if (!response.ok) {
                throw new Error(`API call failed: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            const processingTime = Date.now() - startTime;
            
            return this.parseResponse(provider, data, processingTime);
            
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }
    
    /**
     * Schedule model call for GitHub Actions execution
     */
    async scheduleForGitHubActions(model, request) {
        // Create a task file for GitHub Actions to process
        const taskId = this.generateTaskId();
        const task = {
            id: taskId,
            model: model.id,
            provider: model.provider,
            request: request,
            status: 'pending',
            created: new Date().toISOString(),
            priority: request.priority || 'normal'
        };
        
        // Write task to queue
        const queuePath = '.llmxive-system/queue/model-tasks.json';
        let queue = await this.fileManager.readJSON(queuePath) || { tasks: [] };
        
        queue.tasks.push(task);
        queue.lastUpdated = new Date().toISOString();
        
        await this.fileManager.writeJSON(queuePath, queue, `Queue model task ${taskId}`);
        
        console.log(`Scheduled model task ${taskId} for GitHub Actions`);
        
        return {
            taskId: taskId,
            status: 'scheduled',
            message: 'Task queued for GitHub Actions execution',
            estimatedProcessingTime: model.avg_processing_time || 30
        };
    }
    
    /**
     * Get API endpoint for provider
     */
    getApiEndpoint(provider, model) {
        switch (provider.id) {
            case 'anthropic':
                return `${provider.api_base_url}/v1/messages`;
            case 'openai':
                return `${provider.api_base_url}/v1/chat/completions`;
            case 'google':
                return `${provider.api_base_url}/v1beta/models/${model.id}:generateContent`;
            default:
                throw new Error(`Unknown provider: ${provider.id}`);
        }
    }
    
    /**
     * Get authorization header for provider
     */
    getAuthHeader(provider, apiKey) {
        switch (provider.id) {
            case 'anthropic':
                return `Bearer ${apiKey}`;
            case 'openai':
                return `Bearer ${apiKey}`;
            case 'google':
                return `Bearer ${apiKey}`;
            default:
                return `Bearer ${apiKey}`;
        }
    }
    
    /**
     * Get provider-specific headers
     */
    getProviderHeaders(provider) {
        switch (provider.id) {
            case 'anthropic':
                return {
                    'anthropic-version': '2023-06-01'
                };
            default:
                return {};
        }
    }
    
    /**
     * Parse provider response
     */
    parseResponse(provider, data, processingTime) {
        switch (provider.id) {
            case 'anthropic':
                return {
                    content: data.content[0]?.text || '',
                    tokensUsed: {
                        input: data.usage?.input_tokens || 0,
                        output: data.usage?.output_tokens || 0
                    },
                    processingTime: processingTime
                };
            case 'openai':
                return {
                    content: data.choices[0]?.message?.content || '',
                    tokensUsed: {
                        input: data.usage?.prompt_tokens || 0,
                        output: data.usage?.completion_tokens || 0
                    },
                    processingTime: processingTime
                };
            case 'google':
                return {
                    content: data.candidates[0]?.content?.parts[0]?.text || '',
                    tokensUsed: {
                        input: data.usageMetadata?.promptTokenCount || 0,
                        output: data.usageMetadata?.candidatesTokenCount || 0
                    },
                    processingTime: processingTime
                };
            default:
                return {
                    content: data.content || data.text || '',
                    tokensUsed: { input: 0, output: 0 },
                    processingTime: processingTime
                };
        }
    }
    
    /**
     * Check rate limits for provider
     */
    async checkRateLimit(providerId) {
        const limit = this.rateLimits.get(providerId);
        if (!limit) return;
        
        const now = Date.now();
        const timeWindow = 60000; // 1 minute
        
        // Clean old entries
        limit.requests = limit.requests.filter(time => (now - time) < timeWindow);
        
        const provider = this.providersCache.providers[providerId];
        const maxRequests = provider.rate_limits?.requests_per_minute || 60;
        
        if (limit.requests.length >= maxRequests) {
            const oldestRequest = Math.min(...limit.requests);
            const waitTime = timeWindow - (now - oldestRequest);
            throw new Error(`Rate limit exceeded. Wait ${Math.ceil(waitTime / 1000)} seconds.`);
        }
    }
    
    /**
     * Update rate limit tracking
     */
    updateRateLimit(providerId) {
        if (!this.rateLimits.has(providerId)) {
            this.rateLimits.set(providerId, { requests: [] });
        }
        
        this.rateLimits.get(providerId).requests.push(Date.now());
    }
    
    /**
     * Calculate cost for model call
     */
    calculateCost(model, tokensUsed) {
        if (!tokensUsed || !model.cost_per_1k_tokens) {
            return null;
        }
        
        const inputCost = (tokensUsed.input / 1000) * model.cost_per_1k_tokens.input;
        const outputCost = (tokensUsed.output / 1000) * model.cost_per_1k_tokens.output;
        
        return {
            input: inputCost,
            output: outputCost,
            total: inputCost + outputCost
        };
    }
    
    /**
     * Check if error is retryable
     */
    isRetryableError(error) {
        const retryableMessages = [
            'rate limit',
            'timeout',
            'temporary',
            'service unavailable',
            '502',
            '503',
            '504'
        ];
        
        const message = error.message.toLowerCase();
        return retryableMessages.some(msg => message.includes(msg));
    }
    
    /**
     * Log model call for tracking and debugging
     */
    async logModelCall(modelId, prompt, response, status, error = null) {
        const logEntry = {
            modelId: modelId,
            status: status,
            promptLength: prompt.length,
            responseLength: response?.content?.length || 0,
            tokensUsed: response?.tokensUsed || null,
            processingTime: response?.processingTime || null,
            error: error,
            timestamp: new Date().toISOString()
        };
        
        try {
            await this.fileManager.appendToLog('.llmxive-system/logs/model-calls.json', logEntry);
        } catch (logError) {
            console.error('Failed to log model call:', logError);
        }
    }
    
    /**
     * Generate unique task ID
     */
    generateTaskId() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2, 8);
        return `task_${timestamp}_${random}`;
    }
    
    /**
     * Sleep utility for delays
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Get model statistics
     */
    async getModelStatistics() {
        try {
            const logs = await this.fileManager.readJSON('.llmxive-system/logs/model-calls.json');
            if (!logs || !logs.entries) {
                return { totalCalls: 0, successRate: 0, averageProcessingTime: 0 };
            }
            
            const entries = logs.entries;
            const totalCalls = entries.length;
            const successfulCalls = entries.filter(entry => entry.status === 'success').length;
            const successRate = totalCalls > 0 ? (successfulCalls / totalCalls) * 100 : 0;
            
            const processingTimes = entries
                .filter(entry => entry.processingTime)
                .map(entry => entry.processingTime);
            
            const averageProcessingTime = processingTimes.length > 0
                ? processingTimes.reduce((sum, time) => sum + time, 0) / processingTimes.length
                : 0;
            
            return {
                totalCalls,
                successfulCalls,
                successRate: Math.round(successRate * 100) / 100,
                averageProcessingTime: Math.round(averageProcessingTime)
            };
            
        } catch (error) {
            console.error('Failed to get model statistics:', error);
            return { totalCalls: 0, successRate: 0, averageProcessingTime: 0 };
        }
    }
    
    /**
     * Add new model to registry (ADMIN ONLY)
     */
    async addModel(modelConfig) {
        try {
            // Security check - only admins can add models
            if (this.accessControl) {
                this.accessControl.requirePermission('model.create', 'add new AI model');
                this.accessControl.logAccessEvent('model.add', modelConfig.id, true, { modelConfig });
            }
            
            await this.loadConfigurations();
            
            // Validate model configuration
            this.validateModelConfig(modelConfig);
            
            // Check if model already exists
            if (this.modelsCache.models[modelConfig.id]) {
                throw new Error(`Model '${modelConfig.id}' already exists`);
            }
            
            // Add model to registry
            this.modelsCache.models[modelConfig.id] = {
                ...modelConfig,
                addedAt: new Date().toISOString(),
                addedBy: this.accessControl?.client?.getCurrentUser()?.login || 'system',
                status: 'inactive' // Start as inactive for safety
            };
            
            // Save updated configuration
            await this.fileManager.writeJSON(this.modelsPath, this.modelsCache);
            
            console.log(`Model '${modelConfig.id}' added successfully`);
            return { success: true, modelId: modelConfig.id };
            
        } catch (error) {
            if (this.accessControl) {
                this.accessControl.logAccessEvent('model.add', modelConfig?.id || 'unknown', false, { error: error.message });
            }
            console.error('Failed to add model:', error);
            throw error;
        }
    }
    
    /**
     * Update existing model configuration (ADMIN ONLY)
     */
    async updateModel(modelId, updates) {
        try {
            // Security check - only admins can modify models
            if (this.accessControl) {
                this.accessControl.requirePermission('model.update', 'modify AI model');
                
                // Additional security for critical models
                if (!this.accessControl.canModifyModel(modelId, 'update')) {
                    throw new AccessControlError(
                        'Insufficient permissions to modify this model',
                        'model.update.critical',
                        this.accessControl.userRole
                    );
                }
                
                this.accessControl.logAccessEvent('model.update', modelId, true, { updates });
            }
            
            await this.loadConfigurations();
            
            // Check if model exists
            if (!this.modelsCache.models[modelId]) {
                throw new Error(`Model '${modelId}' not found`);
            }
            
            // Validate updates
            this.validateModelUpdates(updates);
            
            // Apply updates
            const currentModel = this.modelsCache.models[modelId];
            const updatedModel = {
                ...currentModel,
                ...updates,
                updatedAt: new Date().toISOString(),
                updatedBy: this.accessControl?.client?.getCurrentUser()?.login || 'system'
            };
            
            // Validate final configuration
            this.validateModelConfig(updatedModel);
            
            this.modelsCache.models[modelId] = updatedModel;
            
            // Save updated configuration
            await this.fileManager.writeJSON(this.modelsPath, this.modelsCache);
            
            console.log(`Model '${modelId}' updated successfully`);
            return { success: true, modelId, updatedModel };
            
        } catch (error) {
            if (this.accessControl) {
                this.accessControl.logAccessEvent('model.update', modelId, false, { error: error.message });
            }
            console.error('Failed to update model:', error);
            throw error;
        }
    }
    
    /**
     * Remove model from registry (ADMIN ONLY)
     */
    async removeModel(modelId) {
        try {
            // Security check - only admins can remove models
            if (this.accessControl) {
                this.accessControl.requirePermission('model.delete', 'remove AI model');
                
                // Additional security for critical models
                if (!this.accessControl.canModifyModel(modelId, 'remove')) {
                    throw new AccessControlError(
                        'Insufficient permissions to remove this model',
                        'model.delete.critical',
                        this.accessControl.userRole
                    );
                }
                
                this.accessControl.logAccessEvent('model.remove', modelId, true);
            }
            
            await this.loadConfigurations();
            
            // Check if model exists
            if (!this.modelsCache.models[modelId]) {
                throw new Error(`Model '${modelId}' not found`);
            }
            
            // Check if model is currently in use
            const activeJobs = await this.getActiveModelJobs(modelId);
            if (activeJobs.length > 0) {
                throw new Error(`Cannot remove model '${modelId}': ${activeJobs.length} active jobs`);
            }
            
            // Archive model instead of deleting (for audit trail)
            const archivedModel = {
                ...this.modelsCache.models[modelId],
                status: 'archived',
                archivedAt: new Date().toISOString(),
                archivedBy: this.accessControl?.client?.getCurrentUser()?.login || 'system'
            };
            
            // Save to archive
            await this.archiveModel(modelId, archivedModel);
            
            // Remove from active registry
            delete this.modelsCache.models[modelId];
            
            // Save updated configuration
            await this.fileManager.writeJSON(this.modelsPath, this.modelsCache);
            
            console.log(`Model '${modelId}' removed successfully`);
            return { success: true, modelId, archived: true };
            
        } catch (error) {
            if (this.accessControl) {
                this.accessControl.logAccessEvent('model.remove', modelId, false, { error: error.message });
            }
            console.error('Failed to remove model:', error);
            throw error;
        }
    }
    
    /**
     * Configure model settings (ADMIN ONLY)
     */
    async configureModel(modelId, configuration) {
        try {
            // Security check - only admins can configure models
            if (this.accessControl) {
                this.accessControl.requirePermission('model.configure', 'configure AI model');
                this.accessControl.logAccessEvent('model.configure', modelId, true, { configuration });
            }
            
            await this.loadConfigurations();
            
            // Check if model exists
            if (!this.modelsCache.models[modelId]) {
                throw new Error(`Model '${modelId}' not found`);
            }
            
            // Validate configuration
            this.validateModelConfiguration(configuration);
            
            // Apply configuration
            this.modelsCache.models[modelId].configuration = {
                ...this.modelsCache.models[modelId].configuration,
                ...configuration,
                updatedAt: new Date().toISOString(),
                updatedBy: this.accessControl?.client?.getCurrentUser()?.login || 'system'
            };
            
            // Save updated configuration
            await this.fileManager.writeJSON(this.modelsPath, this.modelsCache);
            
            console.log(`Model '${modelId}' configured successfully`);
            return { success: true, modelId, configuration };
            
        } catch (error) {
            if (this.accessControl) {
                this.accessControl.logAccessEvent('model.configure', modelId, false, { error: error.message });
            }
            console.error('Failed to configure model:', error);
            throw error;
        }
    }
    
    /**
     * Validate model configuration
     */
    validateModelConfig(config) {
        const required = ['id', 'name', 'provider', 'modelName'];
        for (const field of required) {
            if (!config[field]) {
                throw new Error(`Model configuration missing required field: ${field}`);
            }
        }
        
        // Validate provider exists
        if (!this.providersCache.providers[config.provider]) {
            throw new Error(`Unknown provider: ${config.provider}`);
        }
        
        // Validate model ID format
        if (!/^[a-z0-9\-_]+$/i.test(config.id)) {
            throw new Error('Model ID must contain only alphanumeric characters, hyphens, and underscores');
        }
    }
    
    /**
     * Validate model updates
     */
    validateModelUpdates(updates) {
        // Don't allow changing core fields
        const immutableFields = ['id', 'addedAt', 'addedBy'];
        for (const field of immutableFields) {
            if (field in updates) {
                throw new Error(`Cannot modify immutable field: ${field}`);
            }
        }
    }
    
    /**
     * Validate model configuration settings
     */
    validateModelConfiguration(config) {
        if (config.temperature !== undefined) {
            if (typeof config.temperature !== 'number' || config.temperature < 0 || config.temperature > 2) {
                throw new Error('Temperature must be a number between 0 and 2');
            }
        }
        
        if (config.maxTokens !== undefined) {
            if (!Number.isInteger(config.maxTokens) || config.maxTokens < 1) {
                throw new Error('maxTokens must be a positive integer');
            }
        }
        
        if (config.topP !== undefined) {
            if (typeof config.topP !== 'number' || config.topP < 0 || config.topP > 1) {
                throw new Error('topP must be a number between 0 and 1');
            }
        }
    }
    
    /**
     * Get active jobs using a specific model
     */
    async getActiveModelJobs(modelId) {
        try {
            const queuePath = '.llmxive-system/queue/model-tasks.json';
            const queue = await this.fileManager.readJSON(queuePath);
            
            if (!queue || !queue.tasks) {
                return [];
            }
            
            return queue.tasks.filter(task => 
                task.model === modelId && 
                ['pending', 'in_progress'].includes(task.status)
            );
            
        } catch (error) {
            console.warn('Could not check active jobs:', error);
            return [];
        }
    }
    
    /**
     * Archive removed model for audit trail
     */
    async archiveModel(modelId, modelData) {
        try {
            const archivePath = '.llmxive-system/archive/models.json';
            let archive = await this.fileManager.readJSON(archivePath);
            
            if (!archive) {
                archive = { archivedModels: {} };
            }
            
            archive.archivedModels[modelId] = modelData;
            
            await this.fileManager.writeJSON(archivePath, archive);
            
        } catch (error) {
            console.warn('Failed to archive model:', error);
            // Don't fail the operation if archiving fails
        }
    }
}

export default ModelManager;