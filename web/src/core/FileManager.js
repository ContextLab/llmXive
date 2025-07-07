/**
 * FileManager - Core file I/O operations with GitHub API
 * 
 * Handles all file operations for the GitHub-native llmXive architecture.
 * Provides caching, rate limiting, and error recovery for repository operations.
 */

class FileManager {
    constructor(githubClient, options = {}) {
        this.github = githubClient;
        this.owner = options.owner || 'ContextLab';
        this.repo = options.repo || 'llmXive';
        this.branch = options.branch || 'main';
        
        // Multi-layer caching
        this.memoryCache = new Map();
        this.cacheTimeout = options.cacheTimeout || 300000; // 5 minutes
        
        // Rate limiting
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.maxConcurrentRequests = options.maxConcurrentRequests || 3;
        this.requestDelay = options.requestDelay || 1000; // 1 second between requests
        
        // Error tracking
        this.consecutiveErrors = 0;
        this.maxConsecutiveErrors = options.maxConsecutiveErrors || 5;
        
        this.initializeLocalStorage();
    }
    
    /**
     * Initialize localStorage cache for persistent caching
     */
    initializeLocalStorage() {
        try {
            // Check if localStorage is available
            if (typeof localStorage !== 'undefined') {
                this.localStorageAvailable = true;
                this.localStoragePrefix = 'llmxive_v2_cache_';
            } else {
                this.localStorageAvailable = false;
                console.warn('localStorage not available, using memory cache only');
            }
        } catch (error) {
            this.localStorageAvailable = false;
            console.warn('localStorage access failed, using memory cache only:', error);
        }
    }
    
    /**
     * Generate cache key for file path
     */
    getCacheKey(filePath) {
        return `${this.owner}/${this.repo}/${this.branch}/${filePath}`;
    }
    
    /**
     * Get data from multi-layer cache
     */
    getFromCache(filePath) {
        const cacheKey = this.getCacheKey(filePath);
        
        // Try memory cache first (fastest)
        if (this.memoryCache.has(cacheKey)) {
            const item = this.memoryCache.get(cacheKey);
            if (item.expires > Date.now()) {
                return { data: item.data, source: 'memory' };
            }
            this.memoryCache.delete(cacheKey);
        }
        
        // Try localStorage cache
        if (this.localStorageAvailable) {
            try {
                const stored = localStorage.getItem(this.localStoragePrefix + cacheKey);
                if (stored) {
                    const item = JSON.parse(stored);
                    if (item.expires > Date.now()) {
                        // Promote to memory cache
                        this.setMemoryCache(cacheKey, item.data, item.expires);
                        return { data: item.data, source: 'localStorage' };
                    }
                    localStorage.removeItem(this.localStoragePrefix + cacheKey);
                }
            } catch (error) {
                console.warn('Error reading from localStorage cache:', error);
            }
        }
        
        return null;
    }
    
    /**
     * Set data in multi-layer cache
     */
    setCache(filePath, data, ttl = this.cacheTimeout) {
        const cacheKey = this.getCacheKey(filePath);
        const expires = Date.now() + ttl;
        
        // Set memory cache
        this.setMemoryCache(cacheKey, data, expires);
        
        // Set localStorage cache
        if (this.localStorageAvailable) {
            try {
                const item = { data, expires };
                localStorage.setItem(this.localStoragePrefix + cacheKey, JSON.stringify(item));
            } catch (error) {
                console.warn('Error writing to localStorage cache:', error);
            }
        }
    }
    
    /**
     * Set memory cache with size limit
     */
    setMemoryCache(cacheKey, data, expires) {
        // Limit memory cache size to prevent memory leaks
        if (this.memoryCache.size >= 1000) {
            // Remove oldest entries
            const keys = Array.from(this.memoryCache.keys());
            for (let i = 0; i < 100; i++) {
                this.memoryCache.delete(keys[i]);
            }
        }
        
        this.memoryCache.set(cacheKey, { data, expires });
    }
    
    /**
     * Clear cache for specific file or all files
     */
    clearCache(filePath = null) {
        if (filePath) {
            const cacheKey = this.getCacheKey(filePath);
            this.memoryCache.delete(cacheKey);
            
            if (this.localStorageAvailable) {
                try {
                    localStorage.removeItem(this.localStoragePrefix + cacheKey);
                } catch (error) {
                    console.warn('Error clearing localStorage cache:', error);
                }
            }
        } else {
            // Clear all cache
            this.memoryCache.clear();
            
            if (this.localStorageAvailable) {
                try {
                    const keys = Object.keys(localStorage);
                    keys.forEach(key => {
                        if (key.startsWith(this.localStoragePrefix)) {
                            localStorage.removeItem(key);
                        }
                    });
                } catch (error) {
                    console.warn('Error clearing all localStorage cache:', error);
                }
            }
        }
    }
    
    /**
     * Add request to queue for rate limiting
     */
    async queueRequest(requestFn) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({ requestFn, resolve, reject });
            this.processQueue();
        });
    }
    
    /**
     * Process queued requests with rate limiting
     */
    async processQueue() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) {
            return;
        }
        
        this.isProcessingQueue = true;
        
        try {
            while (this.requestQueue.length > 0) {
                const { requestFn, resolve, reject } = this.requestQueue.shift();
                
                try {
                    const result = await requestFn();
                    resolve(result);
                    this.consecutiveErrors = 0; // Reset error count on success
                } catch (error) {
                    this.consecutiveErrors++;
                    console.error('Request failed:', error);
                    
                    if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                        console.error('Too many consecutive errors, pausing requests');
                        // Exponential backoff
                        await this.sleep(Math.min(30000, 1000 * Math.pow(2, this.consecutiveErrors - this.maxConsecutiveErrors)));
                    }
                    
                    reject(error);
                }
                
                // Rate limiting delay
                if (this.requestQueue.length > 0) {
                    await this.sleep(this.requestDelay);
                }
            }
        } finally {
            this.isProcessingQueue = false;
        }
    }
    
    /**
     * Sleep utility for delays
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Read JSON file from repository
     */
    async readJSON(filePath, useCache = true) {
        try {
            // Check cache first
            if (useCache) {
                const cached = this.getFromCache(filePath);
                if (cached) {
                    console.log(`Cache hit for ${filePath} (${cached.source})`);
                    return cached.data;
                }
            }
            
            // Queue the GitHub API request
            const result = await this.queueRequest(async () => {
                console.log(`Fetching ${filePath} from GitHub API`);
                const response = await this.github.rest.repos.getContent({
                    owner: this.owner,
                    repo: this.repo,
                    path: filePath,
                    ref: this.branch
                });
                
                if (response.data.type !== 'file') {
                    throw new Error(`Expected file but got ${response.data.type}: ${filePath}`);
                }
                
                const content = atob(response.data.content);
                return JSON.parse(content);
            });
            
            // Cache the result
            if (useCache) {
                this.setCache(filePath, result);
            }
            
            return result;
            
        } catch (error) {
            if (error.status === 404) {
                console.log(`File not found: ${filePath}`);
                return null;
            }
            console.error(`Error reading JSON file ${filePath}:`, error);
            throw error;
        }
    }
    
    /**
     * Write JSON file to repository
     */
    async writeJSON(filePath, data, commitMessage = null, createIfNotExists = true) {
        try {
            const jsonContent = JSON.stringify(data, null, 2);
            const base64Content = btoa(jsonContent);
            
            // Generate commit message if not provided
            if (!commitMessage) {
                commitMessage = `Update ${filePath}`;
            }
            
            // Check if file exists to get SHA for update
            let sha = null;
            if (!createIfNotExists) {
                try {
                    const existing = await this.queueRequest(async () => {
                        return await this.github.rest.repos.getContent({
                            owner: this.owner,
                            repo: this.repo,
                            path: filePath,
                            ref: this.branch
                        });
                    });
                    sha = existing.data.sha;
                } catch (error) {
                    if (error.status === 404 && !createIfNotExists) {
                        throw new Error(`File ${filePath} does not exist and createIfNotExists is false`);
                    }
                }
            } else {
                // Try to get existing SHA for update
                try {
                    const existing = await this.queueRequest(async () => {
                        return await this.github.rest.repos.getContent({
                            owner: this.owner,
                            repo: this.repo,
                            path: filePath,
                            ref: this.branch
                        });
                    });
                    sha = existing.data.sha;
                } catch (error) {
                    // File doesn't exist, will create new
                    if (error.status !== 404) {
                        throw error;
                    }
                }
            }
            
            // Write/update the file
            const result = await this.queueRequest(async () => {
                const params = {
                    owner: this.owner,
                    repo: this.repo,
                    path: filePath,
                    message: commitMessage,
                    content: base64Content,
                    branch: this.branch
                };
                
                if (sha) {
                    params.sha = sha;
                }
                
                return await this.github.rest.repos.createOrUpdateFileContents(params);
            });
            
            // Update cache
            this.setCache(filePath, data);
            
            console.log(`Successfully wrote ${filePath}`);
            return result.data;
            
        } catch (error) {
            console.error(`Error writing JSON file ${filePath}:`, error);
            throw error;
        }
    }
    
    /**
     * Append to log file with structured logging
     */
    async appendToLog(logPath, entry, maxLogSize = 10000) {
        try {
            // Read existing log
            let logData = await this.readJSON(logPath, false) || { entries: [], created: new Date().toISOString() };
            
            // Add new entry
            const logEntry = {
                timestamp: new Date().toISOString(),
                ...entry
            };
            
            logData.entries.push(logEntry);
            logData.lastUpdated = new Date().toISOString();
            
            // Trim log if too large
            if (logData.entries.length > maxLogSize) {
                const excess = logData.entries.length - maxLogSize;
                logData.entries = logData.entries.slice(excess);
                logData.trimmed = (logData.trimmed || 0) + excess;
            }
            
            // Write back to file
            await this.writeJSON(logPath, logData, `Append to log: ${logEntry.type || 'entry'}`);
            
            return logEntry;
            
        } catch (error) {
            console.error(`Error appending to log ${logPath}:`, error);
            throw error;
        }
    }
    
    /**
     * Check if file exists
     */
    async fileExists(filePath) {
        try {
            await this.queueRequest(async () => {
                return await this.github.rest.repos.getContent({
                    owner: this.owner,
                    repo: this.repo,
                    path: filePath,
                    ref: this.branch
                });
            });
            return true;
        } catch (error) {
            if (error.status === 404) {
                return false;
            }
            throw error;
        }
    }
    
    /**
     * List files in directory
     */
    async listDirectory(dirPath) {
        try {
            const result = await this.queueRequest(async () => {
                return await this.github.rest.repos.getContent({
                    owner: this.owner,
                    repo: this.repo,
                    path: dirPath,
                    ref: this.branch
                });
            });
            
            if (!Array.isArray(result.data)) {
                throw new Error(`Expected directory but got file: ${dirPath}`);
            }
            
            return result.data.map(item => ({
                name: item.name,
                path: item.path,
                type: item.type,
                size: item.size
            }));
            
        } catch (error) {
            if (error.status === 404) {
                return [];
            }
            console.error(`Error listing directory ${dirPath}:`, error);
            throw error;
        }
    }
    
    /**
     * Create directory by adding a .gitkeep file
     */
    async createDirectory(dirPath) {
        const gitkeepPath = `${dirPath}/.gitkeep`;
        
        if (await this.fileExists(gitkeepPath)) {
            return; // Directory already exists
        }
        
        try {
            await this.queueRequest(async () => {
                return await this.github.rest.repos.createOrUpdateFileContents({
                    owner: this.owner,
                    repo: this.repo,
                    path: gitkeepPath,
                    message: `Create directory ${dirPath}`,
                    content: btoa(''), // Empty file
                    branch: this.branch
                });
            });
            
            console.log(`Created directory: ${dirPath}`);
            
        } catch (error) {
            console.error(`Error creating directory ${dirPath}:`, error);
            throw error;
        }
    }
    
    /**
     * Get repository statistics
     */
    getStats() {
        return {
            memoryCacheSize: this.memoryCache.size,
            queueLength: this.requestQueue.length,
            consecutiveErrors: this.consecutiveErrors,
            isProcessingQueue: this.isProcessingQueue
        };
    }
}

export default FileManager;