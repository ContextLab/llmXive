/**
 * ModelManager - Manages AI model integration and execution
 * 
 * Handles model selection, API calls, and response processing for the
 * llmXive v2.0 automated review system. Designed for client-side execution
 * with GitHub Actions for server-side model calls.
 */

class ModelManager {
    constructor(fileManager, systemConfig) {
        this.fileManager = fileManager;
        this.systemConfig = systemConfig;
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
}

export default ModelManager;