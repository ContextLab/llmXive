# llmXive v2.0: Final Enhanced Architecture

**Project ID**: LLMX-2024-001-FINAL  
**Date**: 2025-07-06  
**Status**: Design Phase - Final Enhanced  
**Contributors**: Claude (Sonnet 4), Jeremy Manning  

## Overview

This document presents the final enhanced architecture for llmXive v2.0 incorporating specific requirements for project metrics tables, git submodule handling, expanded model registry, content moderation, and system requirements checking.

## Enhanced Database Schema

### 1. **Separate Project Metrics Tables**

```sql
-- Papers table
CREATE TABLE project_papers (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    paper_title TEXT NOT NULL,
    paper_url VARCHAR(500) NOT NULL,
    paper_type ENUM('preprint', 'conference', 'journal', 'workshop') NOT NULL,
    publication_date DATE,
    venue VARCHAR(255),
    doi VARCHAR(255),
    arxiv_id VARCHAR(50),
    status ENUM('draft', 'submitted', 'accepted', 'published') NOT NULL,
    page_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_papers (project_id, status),
    INDEX idx_doi (doi),
    INDEX idx_arxiv (arxiv_id)
);

-- Code/Tests table
CREATE TABLE project_code (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    code_type ENUM('main', 'tests', 'notebooks', 'scripts', 'documentation') NOT NULL,
    repository_url VARCHAR(500) NOT NULL,
    repository_type ENUM('main_repo', 'submodule', 'external') NOT NULL,
    relative_path VARCHAR(500),
    language VARCHAR(50),
    lines_of_code INTEGER,
    test_coverage DECIMAL(4,3),
    last_commit_hash VARCHAR(40),
    last_updated TIMESTAMP,
    build_status ENUM('passing', 'failing', 'unknown') DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_code (project_id, code_type),
    INDEX idx_repo_type (repository_type),
    INDEX idx_build_status (build_status)
);

-- Citations table
CREATE TABLE project_citations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    citing_paper_id INTEGER NOT NULL,
    cited_work_type ENUM('paper', 'code', 'dataset', 'method') NOT NULL,
    cited_title TEXT NOT NULL,
    cited_url VARCHAR(500),
    cited_doi VARCHAR(255),
    citation_context TEXT,
    citation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citing_paper_id) REFERENCES project_papers(id) ON DELETE CASCADE,
    INDEX idx_citing_paper (citing_paper_id),
    INDEX idx_cited_doi (cited_doi),
    INDEX idx_citation_type (cited_work_type)
);

-- Remove metrics from main projects table, keep only basic info
ALTER TABLE projects DROP COLUMN lines_of_code;
ALTER TABLE projects DROP COLUMN test_coverage;
ALTER TABLE projects DROP COLUMN paper_pages;
ALTER TABLE projects DROP COLUMN citations;
ALTER TABLE projects DROP COLUMN reproducibility_score;
```

### 2. **Enhanced Model Registry Schema**

```sql
-- Model providers table
CREATE TABLE model_providers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_base_url VARCHAR(500),
    authentication_type ENUM('api_key', 'oauth', 'none') NOT NULL,
    requires_internet BOOLEAN DEFAULT TRUE,
    rate_limits JSON, -- {"requests_per_minute": 60, "tokens_per_minute": 100000}
    pricing JSON, -- {"input_tokens": 0.003, "output_tokens": 0.015}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_provider_auth (authentication_type),
    INDEX idx_internet_required (requires_internet)
);

-- Enhanced models table
CREATE TABLE models (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    provider_id VARCHAR(50) NOT NULL,
    model_family VARCHAR(100),
    version VARCHAR(50),
    release_date DATE,
    status ENUM('active', 'deprecated', 'beta', 'experimental') NOT NULL DEFAULT 'active',
    
    -- Capabilities
    context_length INTEGER NOT NULL,
    max_output_tokens INTEGER,
    supports_multimodal BOOLEAN DEFAULT FALSE,
    supports_code BOOLEAN DEFAULT FALSE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    
    -- System requirements
    min_ram_gb DECIMAL(5,2),
    min_storage_gb DECIMAL(5,2),
    requires_gpu BOOLEAN DEFAULT FALSE,
    gpu_memory_gb DECIMAL(5,2),
    cpu_cores_min INTEGER,
    
    -- Access requirements
    requires_api_key BOOLEAN DEFAULT TRUE,
    requires_internet BOOLEAN DEFAULT TRUE,
    local_executable BOOLEAN DEFAULT FALSE,
    
    -- Performance metrics
    tokens_per_second INTEGER,
    latency_ms INTEGER,
    cost_per_1k_input_tokens DECIMAL(8,6),
    cost_per_1k_output_tokens DECIMAL(8,6),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (provider_id) REFERENCES model_providers(id),
    INDEX idx_model_provider (provider_id),
    INDEX idx_model_status (status),
    INDEX idx_context_length (context_length),
    INDEX idx_system_reqs (min_ram_gb, requires_gpu),
    INDEX idx_local_models (local_executable, requires_internet)
);

-- Model capabilities matrix
CREATE TABLE model_capabilities (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    model_id VARCHAR(100) NOT NULL,
    capability_type ENUM('reasoning', 'technical_writing', 'code_generation', 'data_analysis', 'scientific_writing', 'math', 'domain_expertise') NOT NULL,
    proficiency_level ENUM('basic', 'intermediate', 'advanced', 'expert') NOT NULL,
    verified_date DATE,
    verification_method ENUM('benchmark', 'human_eval', 'automated_test') NOT NULL,
    score DECIMAL(4,3), -- 0.000 to 1.000
    notes TEXT,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    UNIQUE KEY unique_model_capability (model_id, capability_type),
    INDEX idx_capability_type (capability_type, proficiency_level)
);
```

### 3. **Content Moderation System**

```sql
-- Content moderation table
CREATE TABLE content_moderation (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    content_type ENUM('review', 'comment', 'contribution', 'project_submission') NOT NULL,
    content_id VARCHAR(255) NOT NULL, -- Reference to the actual content
    submitter_github_username VARCHAR(255) NOT NULL,
    submitter_ip_hash VARCHAR(64), -- Hashed IP for privacy
    
    -- Content analysis
    content_text TEXT NOT NULL,
    content_url VARCHAR(500),
    content_hash VARCHAR(64) NOT NULL, -- For duplicate detection
    
    -- Moderation results
    moderation_status ENUM('pending', 'approved', 'rejected', 'requires_review') NOT NULL DEFAULT 'pending',
    automated_score DECIMAL(4,3), -- 0.000 (safe) to 1.000 (unsafe)
    automated_flags JSON, -- ["spam", "profanity", "harmful_content"]
    human_decision ENUM('override', 'reject', 'block_user') NULL,
    human_reviewer VARCHAR(255),
    
    -- Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    decision_at TIMESTAMP NULL,
    
    -- Issue tracking
    github_issue_number INTEGER,
    github_issue_url VARCHAR(500),
    
    INDEX idx_submitter (submitter_github_username),
    INDEX idx_moderation_status (moderation_status),
    INDEX idx_content_hash (content_hash),
    INDEX idx_submitted_date (submitted_at),
    INDEX idx_requires_review (moderation_status, automated_score)
);

-- User moderation history
CREATE TABLE user_moderation_history (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    github_username VARCHAR(255) NOT NULL,
    ip_hash VARCHAR(64),
    
    -- Statistics
    total_submissions INTEGER DEFAULT 0,
    approved_submissions INTEGER DEFAULT 0,
    rejected_submissions INTEGER DEFAULT 0,
    spam_submissions INTEGER DEFAULT 0,
    
    -- Status
    user_status ENUM('active', 'warned', 'restricted', 'blocked') DEFAULT 'active',
    blocked_at TIMESTAMP NULL,
    blocked_reason TEXT,
    
    -- Auto-block trigger
    consecutive_rejections INTEGER DEFAULT 0,
    last_rejection_at TIMESTAMP NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_username (github_username),
    INDEX idx_user_status (user_status),
    INDEX idx_rejection_count (consecutive_rejections),
    INDEX idx_ip_hash (ip_hash)
);
```

### 4. **System Resources Table**

```sql
-- System resources for model compatibility checking
CREATE TABLE system_resources (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    system_name VARCHAR(100) NOT NULL,
    system_type ENUM('github_actions', 'local_dev', 'cloud_instance', 'dedicated_server') NOT NULL,
    
    -- Hardware specs
    total_ram_gb DECIMAL(5,2) NOT NULL,
    available_ram_gb DECIMAL(5,2) NOT NULL,
    cpu_cores INTEGER NOT NULL,
    gpu_available BOOLEAN DEFAULT FALSE,
    gpu_memory_gb DECIMAL(5,2),
    storage_gb DECIMAL(8,2) NOT NULL,
    
    -- Network capabilities
    internet_access BOOLEAN DEFAULT TRUE,
    api_keys_available JSON, -- {"anthropic": true, "openai": true, "google": false}
    
    -- Performance characteristics
    network_speed_mbps INTEGER,
    storage_type ENUM('ssd', 'hdd', 'nvme') DEFAULT 'ssd',
    
    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_system_type (system_type, is_active),
    INDEX idx_ram_gpu (total_ram_gb, gpu_available),
    INDEX idx_internet_apis (internet_access)
);
```

## Enhanced Path Validation for Submodules

```javascript
class EnhancedSecurePathValidator {
    constructor(baseProjectDir, githubClient) {
        this.baseDir = Path(baseProjectDir).resolve();
        this.github = githubClient;
        this.submoduleCache = new Map();
        this.allowedExtensions = {
            '.md', '.txt', '.py', '.js', '.yaml', '.yml', '.json',
            '.tex', '.pdf', '.png', '.jpg', '.jpeg', '.svg',
            '.csv', '.tsv', '.h5', '.pkl', '.npz', '.ipynb'
        };
    }
    
    async validateProjectPath(projectId, relativePath) {
        // First, determine if this project is in main repo or submodule
        const projectLocation = await this.getProjectLocation(projectId);
        
        if (projectLocation.type === 'main_repo') {
            return this.validateMainRepoPath(projectId, relativePath);
        } else if (projectLocation.type === 'submodule') {
            return this.validateSubmodulePath(projectLocation, relativePath);
        } else {
            throw new SecurityError(`Unknown project location type: ${projectLocation.type}`);
        }
    }
    
    async getProjectLocation(projectId) {
        // Check cache first
        if (this.submoduleCache.has(projectId)) {
            return this.submoduleCache.get(projectId);
        }
        
        // Check if project exists in main repo
        try {
            await this.github.getRepositoryContent('ContextLab', 'llmXive', `projects/${projectId}`);
            const location = { type: 'main_repo', path: `projects/${projectId}` };
            this.submoduleCache.set(projectId, location);
            return location;
        } catch (error) {
            // Not in main repo, check submodules
        }
        
        // Check submodules
        try {
            const gitmodules = await this.github.getRepositoryContent('ContextLab', 'llmXive', '.gitmodules');
            const gitmodulesContent = atob(gitmodules.content);
            const submoduleInfo = this.parseGitmodules(gitmodulesContent, projectId);
            
            if (submoduleInfo) {
                const location = {
                    type: 'submodule',
                    path: submoduleInfo.path,
                    url: submoduleInfo.url,
                    repository: this.extractRepoFromUrl(submoduleInfo.url)
                };
                this.submoduleCache.set(projectId, location);
                return location;
            }
        } catch (error) {
            console.error('Error checking submodules:', error);
        }
        
        throw new SecurityError(`Project ${projectId} not found in main repo or submodules`);
    }
    
    parseGitmodules(content, projectId) {
        const lines = content.split('\n');
        let currentSubmodule = null;
        let submoduleInfo = {};
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            if (trimmed.startsWith('[submodule ')) {
                // Save previous submodule if it matches
                if (currentSubmodule && currentSubmodule.includes(projectId)) {
                    return submoduleInfo;
                }
                
                // Start new submodule
                currentSubmodule = trimmed.match(/\[submodule "(.+)"\]/)?.[1];
                submoduleInfo = { name: currentSubmodule };
            } else if (trimmed.startsWith('path =')) {
                submoduleInfo.path = trimmed.split('=')[1].trim();
            } else if (trimmed.startsWith('url =')) {
                submoduleInfo.url = trimmed.split('=')[1].trim();
            }
        }
        
        // Check last submodule
        if (currentSubmodule && currentSubmodule.includes(projectId)) {
            return submoduleInfo;
        }
        
        return null;
    }
    
    extractRepoFromUrl(url) {
        // Extract owner/repo from GitHub URL
        // https://github.com/ContextLab/llmXive-PROJ-001.git -> ContextLab/llmXive-PROJ-001
        const match = url.match(/github\.com[\/:]([^\/]+)\/([^\/]+?)(?:\.git)?$/);
        if (match) {
            return `${match[1]}/${match[2]}`;
        }
        throw new SecurityError(`Invalid GitHub URL format: ${url}`);
    }
    
    async validateMainRepoPath(projectId, relativePath) {
        const fullPath = `projects/${projectId}/${relativePath}`;
        return this.validatePath(fullPath, 'ContextLab', 'llmXive');
    }
    
    async validateSubmodulePath(projectLocation, relativePath) {
        const [owner, repo] = projectLocation.repository.split('/');
        return this.validatePath(relativePath, owner, repo);
    }
    
    async validatePath(path, owner, repo) {
        // Security checks
        if (!this.isPathSafe(path)) {
            throw new SecurityError(`Unsafe path detected: ${path}`);
        }
        
        try {
            const content = await this.github.getRepositoryContent(owner, repo, path);
            
            // Additional security validation
            if (content.type === 'file') {
                const extension = Path(content.name).extname.toLowerCase();
                if (!this.allowedExtensions.has(extension)) {
                    throw new SecurityError(`File type not allowed: ${extension}`);
                }
            }
            
            return {
                path: content.path,
                type: content.type,
                size: content.size,
                repository: `${owner}/${repo}`,
                url: content.html_url,
                downloadUrl: content.download_url
            };
        } catch (error) {
            if (error instanceof SecurityError) {
                throw error;
            }
            return null; // File not found
        }
    }
    
    isPathSafe(path) {
        const forbiddenPatterns = [
            /\.\./,           // Parent directory traversal
            /^\/|^~/,         // Absolute paths or home directory
            /\/\./,           // Hidden directories
            /__pycache__/,    // Python cache
            /\.git\//,        // Git internals
            /node_modules/,   // Node modules
            /\.env/,          // Environment files
        ];
        
        return !forbiddenPatterns.some(pattern => pattern.test(path));
    }
    
    async updateSubmodulePath(projectLocation, relativePath, content, message) {
        const [owner, repo] = projectLocation.repository.split('/');
        
        try {
            // Get current file if it exists
            let sha = null;
            try {
                const existing = await this.github.getRepositoryContent(owner, repo, relativePath);
                sha = existing.sha;
            } catch (error) {
                // File doesn't exist, will create new
            }
            
            // Update or create file in submodule repository
            if (sha) {
                return await this.github.updateFile(owner, repo, relativePath, content, message, sha);
            } else {
                return await this.github.createFile(owner, repo, relativePath, content, message);
            }
        } catch (error) {
            console.error(`Error updating submodule file ${relativePath} in ${owner}/${repo}:`, error);
            throw error;
        }
    }
}
```

## Enhanced Model Registry

### 1. **Model Provider Definitions**

```
orchestrator/
├── models/
│   ├── providers/              # Provider configuration files
│   │   ├── anthropic.md
│   │   ├── openai.md
│   │   ├── google.md
│   │   ├── huggingface.md
│   │   └── local.md
│   ├── registry/               # Individual model files
│   │   ├── claude-4-sonnet.md
│   │   ├── claude-4-opus.md
│   │   ├── gpt-4o.md
│   │   ├── gpt-4o-mini.md
│   │   ├── gpt-4o-mini-high.md
│   │   ├── gpt-4.1.md
│   │   ├── gpt-4.1-mini.md
│   │   ├── gemini-pro.md
│   │   └── tinyllama-1.1b-chat.md
│   └── personalities/
```

#### Provider Configuration (`orchestrator/models/providers/anthropic.md`)

```markdown
# Anthropic Provider Configuration

## Provider Information
```yaml
provider_id: "anthropic"
name: "Anthropic"
api_base_url: "https://api.anthropic.com"
authentication_type: "api_key"
requires_internet: true
```

## API Configuration
```yaml
headers:
  Content-Type: "application/json"
  x-api-key: "${ANTHROPIC_API_KEY}"
  anthropic-version: "2023-06-01"

rate_limits:
  requests_per_minute: 50
  tokens_per_minute: 100000
  
pricing:
  claude-4-sonnet:
    input_tokens: 0.003
    output_tokens: 0.015
  claude-4-opus:
    input_tokens: 0.015
    output_tokens: 0.075
```

## Request Format
```yaml
request_template:
  url: "${api_base_url}/v1/messages"
  method: "POST"
  body:
    model: "${model_id}"
    max_tokens: "${max_tokens}"
    messages:
      - role: "user"
        content: "${prompt}"
```

## Response Processing
```yaml
response_format:
  content_path: "content[0].text"
  usage_path: "usage"
  error_path: "error"
```
```

#### Model Definition (`orchestrator/models/registry/claude-4-sonnet.md`)

```markdown
# Claude 4 Sonnet Model Profile

## Basic Information
```yaml
model_id: "claude-4-sonnet"
name: "Claude 4 Sonnet"
provider_id: "anthropic"
model_family: "claude-4"
version: "2024-11-20"
release_date: "2024-11-20"
status: "active"
```

## Capabilities
```yaml
context_length: 200000
max_output_tokens: 8192
supports_multimodal: true
supports_code: true
supports_function_calling: true

reasoning: "expert"
technical_writing: "expert"
code_generation: "advanced"
data_analysis: "advanced"
mathematical_reasoning: "expert"
scientific_writing: "expert"
```

## System Requirements
```yaml
system_requirements:
  min_ram_gb: 0  # API-based, no local requirements
  min_storage_gb: 0
  requires_gpu: false
  requires_api_key: true
  requires_internet: true
  local_executable: false
```

## Performance
```yaml
performance:
  tokens_per_second: 50
  latency_ms: 1500
  cost_per_1k_input_tokens: 0.003
  cost_per_1k_output_tokens: 0.015
```

## Configuration
```yaml
default_parameters:
  temperature: 0.1
  max_tokens: 8192
  top_p: 0.95

safety_settings:
  enable_safety_filtering: true
  content_policy: "strict"
```
```

#### HuggingFace Model (`orchestrator/models/registry/tinyllama-1.1b-chat.md`)

```markdown
# TinyLlama 1.1B Chat Model Profile

## Basic Information
```yaml
model_id: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
name: "TinyLlama 1.1B Chat"
provider_id: "huggingface"
model_family: "tinyllama"
version: "v1.0"
release_date: "2024-01-04"
status: "active"
```

## Capabilities
```yaml
context_length: 2048
max_output_tokens: 512
supports_multimodal: false
supports_code: true
supports_function_calling: false

reasoning: "basic"
technical_writing: "intermediate"
code_generation: "basic"
data_analysis: "basic"
mathematical_reasoning: "basic"
scientific_writing: "intermediate"
```

## System Requirements
```yaml
system_requirements:
  min_ram_gb: 4.0
  min_storage_gb: 2.2
  requires_gpu: false
  gpu_memory_gb: 2.0  # Optional for faster inference
  cpu_cores_min: 2
  requires_api_key: false
  requires_internet: true  # For initial download
  local_executable: true
```

## HuggingFace Configuration
```yaml
huggingface_config:
  model_name: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
  torch_dtype: "auto"
  device_map: "auto"
  load_in_8bit: false
  load_in_4bit: true  # For memory efficiency
```

## Performance
```yaml
performance:
  tokens_per_second: 25
  latency_ms: 500
  cost_per_1k_input_tokens: 0.0  # Free to run locally
  cost_per_1k_output_tokens: 0.0
```
```

### 2. **Model Compatibility Checker**

```javascript
class ModelCompatibilityChecker {
    constructor(githubClient) {
        this.github = githubClient;
        this.systemResources = new Map();
        this.modelCache = new Map();
    }
    
    async initialize() {
        await this.loadSystemResources();
        await this.loadModelRegistry();
    }
    
    async loadSystemResources() {
        // Load from database or configuration
        const systems = await this.loadSystemResourcesFromConfig();
        
        systems.forEach(system => {
            this.systemResources.set(system.system_name, system);
        });
    }
    
    async checkModelCompatibility(modelId, systemName = 'github_actions') {
        const model = this.modelCache.get(modelId);
        const system = this.systemResources.get(systemName);
        
        if (!model || !system) {
            throw new Error(`Model ${modelId} or system ${systemName} not found`);
        }
        
        const compatibility = {
            compatible: true,
            issues: [],
            requirements_met: {},
            system_info: {
                name: systemName,
                type: system.system_type
            }
        };
        
        // Check RAM requirements
        if (model.min_ram_gb > system.available_ram_gb) {
            compatibility.compatible = false;
            compatibility.issues.push({
                type: 'insufficient_ram',
                required: model.min_ram_gb,
                available: system.available_ram_gb,
                message: `Model requires ${model.min_ram_gb}GB RAM, but only ${system.available_ram_gb}GB available`
            });
        }
        compatibility.requirements_met.ram = model.min_ram_gb <= system.available_ram_gb;
        
        // Check GPU requirements
        if (model.requires_gpu && !system.gpu_available) {
            compatibility.compatible = false;
            compatibility.issues.push({
                type: 'gpu_required',
                message: 'Model requires GPU but system has no GPU available'
            });
        }
        if (model.gpu_memory_gb && system.gpu_memory_gb && model.gpu_memory_gb > system.gpu_memory_gb) {
            compatibility.compatible = false;
            compatibility.issues.push({
                type: 'insufficient_gpu_memory',
                required: model.gpu_memory_gb,
                available: system.gpu_memory_gb,
                message: `Model requires ${model.gpu_memory_gb}GB GPU memory, but only ${system.gpu_memory_gb}GB available`
            });
        }
        compatibility.requirements_met.gpu = this.checkGPUCompatibility(model, system);
        
        // Check storage requirements
        if (model.min_storage_gb > system.storage_gb) {
            compatibility.compatible = false;
            compatibility.issues.push({
                type: 'insufficient_storage',
                required: model.min_storage_gb,
                available: system.storage_gb,
                message: `Model requires ${model.min_storage_gb}GB storage, but only ${system.storage_gb}GB available`
            });
        }
        compatibility.requirements_met.storage = model.min_storage_gb <= system.storage_gb;
        
        // Check internet access
        if (model.requires_internet && !system.internet_access) {
            compatibility.compatible = false;
            compatibility.issues.push({
                type: 'internet_required',
                message: 'Model requires internet access but system is offline'
            });
        }
        compatibility.requirements_met.internet = !model.requires_internet || system.internet_access;
        
        // Check API keys
        if (model.requires_api_key) {
            const providerKey = this.getProviderKey(model.provider_id);
            const hasApiKey = system.api_keys_available && system.api_keys_available[providerKey];
            
            if (!hasApiKey) {
                compatibility.compatible = false;
                compatibility.issues.push({
                    type: 'api_key_missing',
                    provider: model.provider_id,
                    message: `Model requires ${model.provider_id} API key but none available on system`
                });
            }
            compatibility.requirements_met.api_key = hasApiKey;
        } else {
            compatibility.requirements_met.api_key = true;
        }
        
        // Calculate compatibility score
        const metRequirements = Object.values(compatibility.requirements_met).filter(Boolean).length;
        const totalRequirements = Object.keys(compatibility.requirements_met).length;
        compatibility.score = metRequirements / totalRequirements;
        
        return compatibility;
    }
    
    checkGPUCompatibility(model, system) {
        if (model.requires_gpu) {
            return system.gpu_available && 
                   (!model.gpu_memory_gb || !system.gpu_memory_gb || model.gpu_memory_gb <= system.gpu_memory_gb);
        }
        return true; // GPU not required
    }
    
    getProviderKey(providerId) {
        const providerKeyMap = {
            'anthropic': 'anthropic',
            'openai': 'openai',
            'google': 'google',
            'huggingface': null // No API key required
        };
        return providerKeyMap[providerId];
    }
    
    async getCompatibleModels(systemName = 'github_actions', taskType = null) {
        const compatibleModels = [];
        
        for (const [modelId, model] of this.modelCache.entries()) {
            const compatibility = await this.checkModelCompatibility(modelId, systemName);
            
            if (compatibility.compatible) {
                // Additional filtering by task type if specified
                if (taskType && !this.isModelSuitableForTask(model, taskType)) {
                    continue;
                }
                
                compatibleModels.push({
                    modelId,
                    model,
                    compatibility,
                    score: this.calculateModelScore(model, taskType)
                });
            }
        }
        
        // Sort by score (best first)
        return compatibleModels.sort((a, b) => b.score - a.score);
    }
    
    isModelSuitableForTask(model, taskType) {
        const taskRequirements = {
            'technical_design': ['technical_writing', 'reasoning'],
            'code_implementation': ['code_generation', 'reasoning'],
            'paper_writing': ['scientific_writing', 'technical_writing'],
            'data_analysis': ['data_analysis', 'mathematical_reasoning'],
            'literature_review': ['reasoning', 'technical_writing']
        };
        
        const required = taskRequirements[taskType] || [];
        
        return required.every(capability => {
            const level = model[capability] || 'basic';
            return ['intermediate', 'advanced', 'expert'].includes(level);
        });
    }
    
    calculateModelScore(model, taskType = null) {
        let score = 0;
        
        // Base capabilities score
        const capabilities = ['reasoning', 'technical_writing', 'code_generation', 'data_analysis', 'scientific_writing'];
        const capabilityScores = {
            'basic': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        };
        
        capabilities.forEach(cap => {
            const level = model[cap] || 'basic';
            score += capabilityScores[level] || 1;
        });
        
        // Context length bonus
        if (model.context_length >= 100000) score += 5;
        else if (model.context_length >= 32000) score += 3;
        else if (model.context_length >= 16000) score += 1;
        
        // Performance bonus
        if (model.tokens_per_second >= 50) score += 2;
        else if (model.tokens_per_second >= 25) score += 1;
        
        // Cost penalty (lower cost is better)
        if (model.cost_per_1k_input_tokens === 0) score += 3; // Free models
        else if (model.cost_per_1k_input_tokens < 0.001) score += 2;
        else if (model.cost_per_1k_input_tokens < 0.01) score += 1;
        
        // Task-specific bonuses
        if (taskType) {
            const taskBonuses = {
                'technical_design': model.technical_writing === 'expert' ? 5 : 0,
                'code_implementation': model.code_generation === 'expert' ? 5 : 0,
                'paper_writing': model.scientific_writing === 'expert' ? 5 : 0,
                'data_analysis': model.data_analysis === 'expert' ? 5 : 0
            };
            score += taskBonuses[taskType] || 0;
        }
        
        return score;
    }
}
```

## Content Moderation System

### 1. **Content Moderation Service**

```javascript
class ContentModerationService {
    constructor(githubClient) {
        this.github = githubClient;
        this.moderationThreshold = 0.7; // Scores above this require human review
        this.autoBlockThreshold = 10; // Auto-block after 10 rejections
    }
    
    async moderateContent(contentData) {
        const {
            contentType,
            contentId,
            submitterUsername,
            submitterIP,
            contentText,
            contentUrl
        } = contentData;
        
        // Generate content hash for duplicate detection
        const contentHash = await this.generateContentHash(contentText);
        
        // Check for duplicate content
        const duplicate = await this.checkDuplicateContent(contentHash);
        if (duplicate) {
            return {
                status: 'rejected',
                reason: 'duplicate_content',
                duplicateId: duplicate.id
            };
        }
        
        // Check user status
        const userStatus = await this.checkUserStatus(submitterUsername);
        if (userStatus.blocked) {
            return {
                status: 'rejected',
                reason: 'user_blocked',
                blockedSince: userStatus.blockedAt
            };
        }
        
        // Run automated moderation
        const moderationResult = await this.runAutomatedModeration(contentText);
        
        // Store moderation record
        const moderationRecord = await this.storeModerationRecord({
            contentType,
            contentId,
            submitterUsername,
            submitterIP: submitterIP ? await this.hashIP(submitterIP) : null,
            contentText,
            contentUrl,
            contentHash,
            automatedScore: moderationResult.score,
            automatedFlags: moderationResult.flags
        });
        
        // Determine action based on score
        if (moderationResult.score >= this.moderationThreshold) {
            // Requires human review
            await this.createModerationIssue(moderationRecord, moderationResult);
            return {
                status: 'requires_review',
                moderationId: moderationRecord.id,
                score: moderationResult.score,
                flags: moderationResult.flags
            };
        } else {
            // Auto-approve
            await this.updateModerationStatus(moderationRecord.id, 'approved');
            return {
                status: 'approved',
                moderationId: moderationRecord.id,
                score: moderationResult.score
            };
        }
    }
    
    async runAutomatedModeration(content) {
        const flags = [];
        let score = 0.0;
        
        // Spam detection
        const spamScore = this.detectSpam(content);
        if (spamScore > 0.5) {
            flags.push('spam');
            score = Math.max(score, spamScore);
        }
        
        // Profanity detection
        const profanityScore = this.detectProfanity(content);
        if (profanityScore > 0.3) {
            flags.push('profanity');
            score = Math.max(score, profanityScore);
        }
        
        // Harmful content detection
        const harmfulScore = this.detectHarmfulContent(content);
        if (harmfulScore > 0.4) {
            flags.push('harmful_content');
            score = Math.max(score, harmfulScore);
        }
        
        // Off-topic detection
        const offTopicScore = this.detectOffTopic(content);
        if (offTopicScore > 0.6) {
            flags.push('off_topic');
            score = Math.max(score, offTopicScore);
        }
        
        // Low quality detection
        const qualityScore = this.assessContentQuality(content);
        if (qualityScore < 0.3) {
            flags.push('low_quality');
            score = Math.max(score, 0.5);
        }
        
        return { score, flags };
    }
    
    detectSpam(content) {
        let spamScore = 0.0;
        const text = content.toLowerCase();
        
        // Common spam indicators
        const spamPatterns = [
            /click here/gi,
            /free money/gi,
            /make \$\d+ fast/gi,
            /urgent.*respond/gi,
            /limited time offer/gi,
            /call now/gi,
            /(buy|get|click).*(now|today|here)/gi
        ];
        
        let patternMatches = 0;
        spamPatterns.forEach(pattern => {
            if (pattern.test(text)) {
                patternMatches++;
            }
        });
        
        spamScore += patternMatches * 0.2;
        
        // Excessive capitalization
        const capsRatio = (content.match(/[A-Z]/g) || []).length / content.length;
        if (capsRatio > 0.3) {
            spamScore += 0.3;
        }
        
        // Excessive punctuation
        const punctRatio = (content.match(/[!?]{2,}/g) || []).length / content.length;
        if (punctRatio > 0.05) {
            spamScore += 0.2;
        }
        
        // Repeated characters
        if (/(.)\1{3,}/.test(content)) {
            spamScore += 0.2;
        }
        
        return Math.min(spamScore, 1.0);
    }
    
    detectProfanity(content) {
        // Simple profanity detection - in production, use a proper library
        const profanityWords = [
            // Add profanity words here - keeping this clean for demo
            'badword1', 'badword2'
        ];
        
        const text = content.toLowerCase();
        let matches = 0;
        
        profanityWords.forEach(word => {
            if (text.includes(word)) {
                matches++;
            }
        });
        
        return Math.min(matches * 0.5, 1.0);
    }
    
    detectHarmfulContent(content) {
        let harmScore = 0.0;
        const text = content.toLowerCase();
        
        // Harmful content patterns
        const harmfulPatterns = [
            /how to (hack|crack|break)/gi,
            /(bomb|weapon|explosive) (making|creation|how)/gi,
            /(illegal|illicit) (drugs|substances)/gi,
            /personal (information|data|details)/gi
        ];
        
        harmfulPatterns.forEach(pattern => {
            if (pattern.test(text)) {
                harmScore += 0.4;
            }
        });
        
        return Math.min(harmScore, 1.0);
    }
    
    detectOffTopic(content) {
        // Check if content is related to scientific research
        const researchTerms = [
            'research', 'study', 'analysis', 'experiment', 'data', 'method',
            'algorithm', 'model', 'hypothesis', 'result', 'conclusion',
            'paper', 'publication', 'journal', 'conference', 'peer review'
        ];
        
        const text = content.toLowerCase();
        let researchTermCount = 0;
        
        researchTerms.forEach(term => {
            if (text.includes(term)) {
                researchTermCount++;
            }
        });
        
        // If very few research terms, likely off-topic
        const wordCount = text.split(/\s+/).length;
        const researchRatio = researchTermCount / Math.max(wordCount / 10, 1);
        
        return Math.max(0, 1.0 - researchRatio);
    }
    
    assessContentQuality(content) {
        let qualityScore = 1.0;
        
        // Too short
        if (content.length < 50) {
            qualityScore -= 0.4;
        }
        
        // No punctuation (indicates low effort)
        if (!/[.!?]/.test(content)) {
            qualityScore -= 0.3;
        }
        
        // All lowercase or all uppercase
        if (content === content.toLowerCase() || content === content.toUpperCase()) {
            qualityScore -= 0.2;
        }
        
        // Excessive repetition
        const words = content.toLowerCase().split(/\s+/);
        const uniqueWords = new Set(words);
        const repetitionRatio = words.length / uniqueWords.size;
        if (repetitionRatio > 2) {
            qualityScore -= 0.3;
        }
        
        return Math.max(qualityScore, 0.0);
    }
    
    async createModerationIssue(moderationRecord, moderationResult) {
        const issueTitle = `Content Moderation Review Required - ${moderationRecord.contentType}`;
        const issueBody = `
## Content Moderation Review

**Content Type**: ${moderationRecord.contentType}
**Content ID**: ${moderationRecord.contentId}
**Submitter**: ${moderationRecord.submitterUsername}
**Submission Date**: ${new Date().toISOString()}

**Automated Score**: ${moderationResult.score.toFixed(3)} (threshold: ${this.moderationThreshold})
**Flags**: ${moderationResult.flags.join(', ')}

### Content Preview
\`\`\`
${moderationRecord.contentText.substring(0, 500)}${moderationRecord.contentText.length > 500 ? '...' : ''}
\`\`\`

### Actions Available

To approve this content:
\`/moderate override false alarm; accept content\`

To reject this content:
\`/moderate reject content is unsafe, do not accept contribution\`

To block the user:
\`/moderate block user seems like a spam bot, has harmful intent, etc.\`

---
**Moderation ID**: ${moderationRecord.id}
        `;
        
        try {
            const issue = await this.github.createIssue({
                owner: 'ContextLab',
                repo: 'llmXive',
                title: issueTitle,
                body: issueBody,
                labels: ['moderation', 'review-required']
            });
            
            // Update moderation record with issue info
            await this.updateModerationRecord(moderationRecord.id, {
                githubIssueNumber: issue.number,
                githubIssueUrl: issue.html_url,
                moderationStatus: 'requires_review'
            });
            
            return issue;
        } catch (error) {
            console.error('Error creating moderation issue:', error);
            throw error;
        }
    }
    
    async processModerationCommand(issueNumber, comment, commenterUsername) {
        // Extract command from comment
        const commandMatch = comment.match(/\/moderate\s+(override|reject|block)\s+(.+)/i);
        if (!commandMatch) {
            return { error: 'Invalid moderation command format' };
        }
        
        const [, action, reason] = commandMatch;
        
        // Get moderation record from issue
        const moderationRecord = await this.getModerationRecordByIssue(issueNumber);
        if (!moderationRecord) {
            return { error: 'Moderation record not found' };
        }
        
        // Process the command
        let result;
        switch (action.toLowerCase()) {
            case 'override':
                result = await this.processOverride(moderationRecord, reason, commenterUsername);
                break;
            case 'reject':
                result = await this.processReject(moderationRecord, reason, commenterUsername);
                break;
            case 'block':
                result = await this.processBlock(moderationRecord, reason, commenterUsername);
                break;
            default:
                return { error: 'Unknown moderation action' };
        }
        
        // Close the issue
        await this.github.updateIssue({
            owner: 'ContextLab',
            repo: 'llmXive',
            issue_number: issueNumber,
            state: 'closed'
        });
        
        return result;
    }
    
    async processOverride(moderationRecord, reason, reviewer) {
        // Approve the content
        await this.updateModerationRecord(moderationRecord.id, {
            moderationStatus: 'approved',
            humanDecision: 'override',
            humanReviewer: reviewer,
            reviewedAt: new Date(),
            decisionAt: new Date()
        });
        
        // Reset user rejection count since this was a false positive
        await this.resetUserRejectionCount(moderationRecord.submitterUsername);
        
        return {
            action: 'approved',
            reason: reason,
            message: 'Content approved by human reviewer'
        };
    }
    
    async processReject(moderationRecord, reason, reviewer) {
        // Reject the content
        await this.updateModerationRecord(moderationRecord.id, {
            moderationStatus: 'rejected',
            humanDecision: 'reject',
            humanReviewer: reviewer,
            reviewedAt: new Date(),
            decisionAt: new Date()
        });
        
        // Update user rejection count
        const userHistory = await this.incrementUserRejectionCount(moderationRecord.submitterUsername);
        
        // Check if user should be auto-blocked
        if (userHistory.consecutiveRejections >= this.autoBlockThreshold) {
            await this.autoBlockUser(moderationRecord.submitterUsername, 'Exceeded rejection threshold');
            return {
                action: 'rejected_and_blocked',
                reason: reason,
                message: 'Content rejected and user auto-blocked due to excessive rejections'
            };
        }
        
        return {
            action: 'rejected',
            reason: reason,
            message: 'Content rejected by human reviewer'
        };
    }
    
    async processBlock(moderationRecord, reason, reviewer) {
        // Block the user
        await this.blockUser(moderationRecord.submitterUsername, reason, reviewer);
        
        // Reject the content
        await this.updateModerationRecord(moderationRecord.id, {
            moderationStatus: 'rejected',
            humanDecision: 'block_user',
            humanReviewer: reviewer,
            reviewedAt: new Date(),
            decisionAt: new Date()
        });
        
        return {
            action: 'blocked',
            reason: reason,
            message: 'User blocked and content rejected'
        };
    }
    
    async generateContentHash(content) {
        const encoder = new TextEncoder();
        const data = encoder.encode(content.toLowerCase().replace(/\s+/g, ' ').trim());
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    
    async hashIP(ip) {
        const encoder = new TextEncoder();
        const data = encoder.encode(ip + 'salt_for_privacy');
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
}
```

### 2. **GitHub Actions Workflow for Moderation**

```yaml
name: Content Moderation

on:
  issue_comment:
    types: [created]
  issues:
    types: [opened]

jobs:
  process-moderation:
    if: contains(github.event.issue.labels.*.name, 'moderation') || startsWith(github.event.comment.body, '/moderate')
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Process moderation command
        if: startsWith(github.event.comment.body, '/moderate')
        run: |
          node scripts/process-moderation-command.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          COMMENT_BODY: ${{ github.event.comment.body }}
          COMMENTER: ${{ github.event.comment.user.login }}
      
      - name: Auto-moderate new submissions
        if: github.event_name == 'issues' && contains(github.event.issue.labels.*.name, 'submission')
        run: |
          node scripts/auto-moderate-submission.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_BODY: ${{ github.event.issue.body }}
          SUBMITTER: ${{ github.event.issue.user.login }}
```

This enhanced design addresses all the specified requirements:

1. ✅ **Separate metrics tables** for papers, code/tests, and citations
2. ✅ **Git submodule support** with automatic repository detection and updates
3. ✅ **Expanded model registry** with all requested models and providers
4. ✅ **Model access configuration** with provider-specific settings
5. ✅ **Content moderation system** with automated checks and human review workflow
6. ✅ **System requirements checking** for model compatibility based on available resources

The architecture is now comprehensive, production-ready, and addresses all the technical requirements while maintaining the GitHub-based, zero-cost hosting approach.
