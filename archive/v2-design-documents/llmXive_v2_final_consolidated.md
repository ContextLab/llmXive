# llmXive v2.0: Final Consolidated Design

**Project ID**: LLMX-2024-001-FINAL-CONSOLIDATED  
**Date**: 2025-07-06  
**Status**: Final Design - Implementation Ready  
**Contributors**: Claude (Sonnet 4), Jeremy Manning, Gemini (Technical Review)

## Overview

This document presents the final, consolidated llmXive v2.0 design that resolves all architectural inconsistencies and provides a coherent, implementable solution for automated scientific discovery using GitHub Pages hosting.

## Architectural Resolution

### **Core Architecture Decision: GitHub-Native with File-Based Persistence**

Based on the technical review, we resolve the architecture contradiction by adopting a **purely GitHub-based approach** that works within GitHub Pages constraints while maintaining full functionality:

- **Frontend**: GitHub Pages static site with client-side JavaScript
- **Backend**: GitHub Actions for server-side processing
- **Database**: JSON files in GitHub repository with caching
- **Authentication**: GitHub OAuth with repository access
- **Storage**: Git repositories with Git LFS for large files

## Unified Project Structure

### **Standard Project Template (Integrating latex-base)**

```
projects/PROJ-XXX-project-name/
├── .llmxive/                       # llmXive metadata (replaces .project-config.json)
│   ├── config.json                 # Project configuration
│   ├── phases.json                 # Phase tracking and status
│   ├── dependencies.json           # Dependency definitions
│   ├── metrics.json                # Project metrics
│   └── moderation.json             # Content moderation history
│
├── .gitignore                      # From latex-base template
├── .gitmodules                     # From latex-base template (if submodules)
├── Dockerfile                      # From latex-base template (customized)
├── LICENSE                         # From latex-base template
├── README.md                       # Project-specific README
├── setup.sh                       # From latex-base template (customized)
│
├── idea/                           # Phase 1: Project ideation
│   ├── initial-idea.md
│   ├── brainstorming/
│   └── reviews/                    # Reviews for idea phase
│       ├── automated/
│       │   ├── idea_01__2024-07-06__A.md
│       │   └── idea_02__2024-07-07__A.md
│       └── manual/
│           ├── jeremy.manning__2024-07-08__M.md
│           └── expert.reviewer__2024-07-09__M.md
│
├── technical-design/               # Phase 2: Technical design
│   ├── main.md                     # Primary design document
│   ├── diagrams/
│   ├── specifications/
│   └── reviews/                    # Reviews for technical design
│       ├── automated/
│       │   ├── design_01__2024-07-10__A.md
│       │   └── design_02__2024-07-11__A.md
│       └── manual/
│           ├── peer.reviewer__2024-07-12__M.md
│           └── technical.expert__2024-07-13__M.md
│
├── implementation-plan/            # Phase 3: Implementation planning
│   ├── main.md                     # Primary implementation plan
│   ├── milestones/
│   ├── tasks/
│   └── reviews/                    # Reviews for implementation plan
│       ├── automated/
│       │   ├── plan_01__2024-07-14__A.md
│       │   └── plan_02__2024-07-15__A.md
│       └── manual/
│           ├── implementation.expert__2024-07-16__M.md
│           └── project.manager__2024-07-17__M.md
│
├── code/                           # From latex-base template
│   ├── src/                        # Source code implementation
│   ├── tests/                      # Test suite
│   ├── notebooks/                  # Jupyter notebooks for analysis
│   ├── scripts/                    # Utility scripts
│   ├── experiments/                # Experimental code
│   └── reviews/                    # Reviews for code
│       ├── automated/
│       │   ├── code_quality_01__2024-07-18__A.md
│       │   └── security_scan_01__2024-07-19__A.md
│       └── manual/
│           ├── code.reviewer__2024-07-20__M.md
│           └── senior.dev__2024-07-21__M.md
│
├── data/                           # From latex-base template
│   ├── raw/                        # Raw datasets
│   ├── processed/                  # Processed datasets
│   ├── synthetic/                  # Generated datasets
│   ├── external/                   # External datasets (linked/cached)
│   └── reviews/                    # Reviews for data
│       ├── automated/
│       │   ├── data_quality_01__2024-07-22__A.md
│       │   └── data_validation_01__2024-07-23__A.md
│       └── manual/
│           ├── data.scientist__2024-07-24__M.md
│           └── domain.expert__2024-07-25__M.md
│
├── paper/                          # From latex-base template
│   ├── main.tex                    # Primary LaTeX document
│   ├── sections/                   # Paper sections
│   │   ├── abstract.tex
│   │   ├── introduction.tex
│   │   ├── methods.tex
│   │   ├── results.tex
│   │   ├── discussion.tex
│   │   └── conclusion.tex
│   ├── figures/                    # Paper figures
│   ├── tables/                     # Paper tables
│   ├── bibliography.bib            # References
│   ├── supplements/                # Supplementary materials
│   ├── drafts/                     # Paper drafts and versions
│   └── reviews/                    # Reviews for paper
│       ├── automated/
│       │   ├── grammar_check_01__2024-07-26__A.md
│       │   └── citation_check_01__2024-07-27__A.md
│       └── manual/
│           ├── peer.reviewer__2024-07-28__M.md
│           └── journal.editor__2024-07-29__M.md
│
└── environment/                    # Computational environment
    ├── docker/                     # Docker configurations
    │   ├── Dockerfile.dev          # Development environment
    │   ├── Dockerfile.prod         # Production environment
    │   └── docker-compose.yml      # Multi-service setup
    ├── conda/                      # Conda environments
    │   ├── environment.yml         # Base environment
    │   └── environment-dev.yml     # Development environment
    └── requirements/               # Python requirements
        ├── base.txt                # Base requirements
        ├── dev.txt                 # Development requirements
        └── prod.txt                # Production requirements
```

## Unified Data Persistence Strategy

### **File-Based Database with GitHub Repository Storage**

Instead of SQL databases, use structured JSON files stored in the GitHub repository:

```
.llmxive-system/                    # System-wide configuration
├── registry/
│   ├── projects.json               # Project registry
│   ├── models.json                 # Model registry
│   ├── providers.json              # Provider configurations
│   └── users.json                  # User moderation history
├── cache/
│   ├── dependencies/               # Cached dependency graphs
│   ├── metrics/                    # Cached project metrics
│   └── api-responses/              # Cached API responses
├── config/
│   ├── pipeline-stages.json        # Pipeline configuration
│   ├── quality-gates.json          # Quality gate definitions
│   ├── review-templates.json       # Review templates
│   └── system-resources.json       # Available system resources
└── logs/
    ├── orchestrator/               # Orchestration logs
    ├── moderation/                 # Moderation decision logs
    └── errors/                     # Error logs
```

### **Project Configuration Schema**

#### `.llmxive/config.json`
```json
{
  "project": {
    "id": "PROJ-001-neural-memory-dynamics",
    "title": "Neural Dynamics of Episodic Memory Formation",
    "description": "Investigation of neural mechanisms underlying episodic memory formation",
    "status": "in_progress",
    "priority": "high",
    "created_date": "2024-01-15T00:00:00Z",
    "last_updated": "2024-07-06T12:00:00Z",
    "estimated_completion": "2024-12-01T00:00:00Z",
    "location": {
      "type": "main_repo",
      "path": "projects/PROJ-001-neural-memory-dynamics",
      "repository": "ContextLab/llmXive",
      "size_mb": 245.6,
      "lfs_objects": 15
    }
  },
  "template": {
    "source": "ContextLab/latex-base",
    "version": "v1.0.0",
    "initialized_date": "2024-01-15T00:00:00Z",
    "customizations": [
      "Added llmXive-specific directories",
      "Enhanced Docker environment",
      "Integrated review system"
    ]
  },
  "contributors": [
    {
      "name": "Claude-4-Sonnet",
      "github_username": "claude-4-sonnet-bot",
      "role": "primary_researcher",
      "type": "ai",
      "contributions": ["design", "implementation", "analysis"],
      "join_date": "2024-01-15T00:00:00Z"
    },
    {
      "name": "Jeremy Manning",
      "github_username": "jeremy.manning",
      "role": "supervisor", 
      "type": "human",
      "contributions": ["oversight", "review", "validation"],
      "join_date": "2024-01-15T00:00:00Z"
    }
  ],
  "computational_requirements": {
    "min_ram_gb": 8,
    "min_storage_gb": 50,
    "gpu_required": false,
    "python_version": "3.9",
    "docker_enabled": true,
    "conda_environment": "environment/conda/environment.yml"
  }
}
```

#### `.llmxive/phases.json`
```json
{
  "idea": {
    "status": "completed",
    "started_date": "2024-01-15T00:00:00Z",
    "completed_date": "2024-01-20T00:00:00Z",
    "artifacts": ["idea/initial-idea.md"],
    "reviews": {
      "required_points": 3.0,
      "current_points": 4.5,
      "automated_reviews": 2,
      "manual_reviews": 3,
      "review_files": [
        "idea/reviews/automated/idea_01__2024-07-06__A.md",
        "idea/reviews/manual/jeremy.manning__2024-07-08__M.md"
      ]
    }
  },
  "technical_design": {
    "status": "completed",
    "started_date": "2024-01-20T00:00:00Z", 
    "completed_date": "2024-02-15T00:00:00Z",
    "artifacts": ["technical-design/main.md"],
    "reviews": {
      "required_points": 5.0,
      "current_points": 7.0,
      "automated_reviews": 4,
      "manual_reviews": 5,
      "review_files": [
        "technical-design/reviews/automated/design_01__2024-07-10__A.md",
        "technical-design/reviews/manual/peer.reviewer__2024-07-12__M.md"
      ]
    }
  },
  "implementation_plan": {
    "status": "completed",
    "started_date": "2024-02-15T00:00:00Z",
    "completed_date": "2024-03-01T00:00:00Z", 
    "artifacts": ["implementation-plan/main.md"],
    "reviews": {
      "required_points": 5.0,
      "current_points": 6.0,
      "automated_reviews": 2,
      "manual_reviews": 4,
      "review_files": [
        "implementation-plan/reviews/automated/plan_01__2024-07-14__A.md",
        "implementation-plan/reviews/manual/implementation.expert__2024-07-16__M.md"
      ]
    }
  },
  "implementation": {
    "status": "in_progress",
    "started_date": "2024-03-01T00:00:00Z",
    "progress": 0.65,
    "artifacts": ["code/src/", "data/processed/", "code/experiments/"],
    "reviews": {
      "required_points": 0,
      "current_points": 0,
      "automated_reviews": 5,
      "manual_reviews": 0,
      "review_files": [
        "code/reviews/automated/code_quality_01__2024-07-18__A.md"
      ]
    }
  },
  "paper": {
    "status": "pending",
    "artifacts": [],
    "reviews": {
      "required_points": 5.0,
      "current_points": 0,
      "automated_reviews": 0,
      "manual_reviews": 0,
      "review_files": []
    }
  }
}
```

#### `.llmxive/dependencies.json`
```json
{
  "project_dependencies": [
    {
      "depends_on_project": "PROJ-000-base-framework",
      "dependency_type": "builds_on",
      "required": true
    }
  ],
  "phase_dependencies": {
    "technical_design": {
      "depends_on_phases": ["idea"],
      "quality_gates": {
        "idea_reviews": {
          "type": "review_points",
          "minimum_value": 3.0,
          "current_value": 4.5,
          "satisfied": true
        }
      }
    },
    "implementation_plan": {
      "depends_on_phases": ["technical_design"],
      "quality_gates": {
        "design_reviews": {
          "type": "review_points", 
          "minimum_value": 5.0,
          "current_value": 7.0,
          "satisfied": true
        }
      }
    },
    "implementation": {
      "depends_on_phases": ["implementation_plan"],
      "quality_gates": {
        "plan_reviews": {
          "type": "review_points",
          "minimum_value": 5.0, 
          "current_value": 6.0,
          "satisfied": true
        }
      }
    },
    "paper": {
      "depends_on_phases": ["implementation_plan"],
      "optional_dependencies": ["implementation"],
      "quality_gates": {
        "plan_reviews": {
          "type": "review_points",
          "minimum_value": 5.0,
          "current_value": 6.0,
          "satisfied": true
        }
      }
    }
  }
}
```

## Enhanced GitHub Client Architecture

### **Unified GitHub Client with File-Based Operations**

```javascript
class UnifiedGitHubClient {
    constructor() {
        this.baseUrl = 'https://api.github.com';
        this.graphqlUrl = 'https://api.github.com/graphql';
        this.token = null;
        
        // Unified components
        this.auth = new SecureAuthManager();
        this.cache = new MultiLayerCache();
        this.rateLimit = new RateLimitManager();
        this.files = new FileManager(this);
        this.projects = new ProjectManager(this);
        this.reviews = new ReviewManager(this);
        this.templates = new TemplateManager(this);
        this.models = new ModelManager(this);
        this.moderation = new ModerationManager(this);
    }
    
    async initialize() {
        await this.auth.initialize();
        this.token = await this.auth.getValidToken();
        
        // Load system configuration
        await this.loadSystemConfig();
        
        // Initialize managers
        await this.projects.initialize();
        await this.models.initialize();
        await this.reviews.initialize();
    }
    
    async loadSystemConfig() {
        try {
            const configs = await Promise.all([
                this.files.readJSON('.llmxive-system/config/pipeline-stages.json'),
                this.files.readJSON('.llmxive-system/config/quality-gates.json'),
                this.files.readJSON('.llmxive-system/registry/models.json'),
                this.files.readJSON('.llmxive-system/registry/providers.json')
            ]);
            
            this.config = {
                pipelineStages: configs[0],
                qualityGates: configs[1], 
                models: configs[2],
                providers: configs[3]
            };
        } catch (error) {
            console.warn('System config not found, using defaults');
            await this.initializeDefaultConfig();
        }
    }
}
```

### **File Manager for JSON-Based Persistence**

```javascript
class FileManager {
    constructor(githubClient) {
        this.github = githubClient;
        this.org = 'ContextLab';
        this.repo = 'llmXive';
        this.cache = new Map();
    }
    
    async readJSON(filePath) {
        // Check cache first
        const cacheKey = `json:${filePath}`;
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 300000) { // 5 minutes
                return cached.data;
            }
        }
        
        try {
            const fileContent = await this.github.apiRequest(`/repos/${this.org}/${this.repo}/contents/${filePath}`);
            const data = JSON.parse(atob(fileContent.content));
            
            // Cache the result
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now(),
                sha: fileContent.sha
            });
            
            return data;
        } catch (error) {
            if (error.status === 404) {
                return null; // File not found
            }
            throw error;
        }
    }
    
    async writeJSON(filePath, data, commitMessage = null) {
        const content = JSON.stringify(data, null, 2);
        const message = commitMessage || `Update ${filePath}`;
        
        try {
            // Check if file exists
            const cached = this.cache.get(`json:${filePath}`);
            const sha = cached?.sha;
            
            let result;
            if (sha) {
                // Update existing file
                result = await this.github.apiRequest(`/repos/${this.org}/${this.repo}/contents/${filePath}`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        message: message,
                        content: btoa(unescape(encodeURIComponent(content))),
                        sha: sha
                    })
                });
            } else {
                // Create new file
                result = await this.github.apiRequest(`/repos/${this.org}/${this.repo}/contents/${filePath}`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        message: message,
                        content: btoa(unescape(encodeURIComponent(content)))
                    })
                });
            }
            
            // Update cache
            this.cache.set(`json:${filePath}`, {
                data: data,
                timestamp: Date.now(),
                sha: result.content.sha
            });
            
            return result;
        } catch (error) {
            console.error(`Error writing JSON file ${filePath}:`, error);
            throw error;
        }
    }
    
    async appendToLog(logFile, entry) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            ...entry
        };
        
        try {
            // Read existing log
            const existingLog = await this.readJSON(logFile) || [];
            
            // Append new entry
            existingLog.push(logEntry);
            
            // Keep only last 1000 entries to prevent file bloat
            if (existingLog.length > 1000) {
                existingLog.splice(0, existingLog.length - 1000);
            }
            
            // Write back
            await this.writeJSON(logFile, existingLog, `Add log entry to ${logFile}`);
            
            return logEntry;
        } catch (error) {
            console.error(`Error appending to log ${logFile}:`, error);
            throw error;
        }
    }
}
```

## Unified Review System

### **Consistent Review Structure Across All Artifacts**

All review directories follow the same structure pattern:

```
{artifact_directory}/reviews/
├── automated/                      # Automated reviews
│   ├── {type}_{number}__{date}__A.md
│   └── {type}_{number}__{date}__A.md
└── manual/                         # Human reviews
    ├── {reviewer}__{date}__M.md
    └── {reviewer}__{date}__M.md
```

### **Review Manager**

```javascript
class ReviewManager {
    constructor(githubClient) {
        this.github = githubClient;
        this.files = githubClient.files;
    }
    
    async submitReview(projectId, artifactType, reviewData) {
        const { reviewerUsername, reviewType, isPositive, score, content } = reviewData;
        
        // Generate review filename
        const date = new Date().toISOString().split('T')[0];
        const reviewerSafe = reviewerUsername.replace(/[^a-zA-Z0-9]/g, '.');
        const isAutomated = reviewData.automated || false;
        const suffix = isAutomated ? 'A' : 'M';
        
        let filename;
        if (isAutomated) {
            // Find next automated review number
            const existingReviews = await this.getExistingReviews(projectId, artifactType, 'automated');
            const reviewNumber = existingReviews.length + 1;
            filename = `${reviewType}_${reviewNumber.toString().padStart(2, '0')}__${date}__${suffix}.md`;
        } else {
            filename = `${reviewerSafe}__${date}__${suffix}.md`;
        }
        
        const reviewPath = `projects/${projectId}/${artifactType}/reviews/${isAutomated ? 'automated' : 'manual'}/${filename}`;
        
        // Create review content
        const reviewContent = this.formatReviewContent(reviewData);
        
        // Save review file
        await this.github.createFile(
            'ContextLab', 'llmXive',
            reviewPath,
            reviewContent,
            `Add ${isAutomated ? 'automated' : 'manual'} review for ${projectId} ${artifactType}`
        );
        
        // Update project phases with new review
        await this.updateProjectReviews(projectId, artifactType, {
            filename: filename,
            path: reviewPath,
            isPositive: isPositive,
            score: score,
            points: isAutomated ? 0.5 : 1.0,
            reviewer: reviewerUsername,
            date: date,
            automated: isAutomated
        });
        
        // Check if phase can now advance
        await this.checkPhaseAdvancement(projectId, artifactType);
        
        return {
            reviewPath: reviewPath,
            filename: filename,
            pointsAwarded: isPositive ? (isAutomated ? 0.5 : 1.0) : 0
        };
    }
    
    async getExistingReviews(projectId, artifactType, reviewType = null) {
        const basePath = `projects/${projectId}/${artifactType}/reviews`;
        const paths = reviewType ? [`${basePath}/${reviewType}`] : [`${basePath}/automated`, `${basePath}/manual`];
        
        const reviews = [];
        for (const path of paths) {
            try {
                const contents = await this.github.apiRequest(`/repos/ContextLab/llmXive/contents/${path}`);
                for (const file of contents) {
                    if (file.type === 'file' && file.name.endsWith('.md')) {
                        reviews.push({
                            filename: file.name,
                            path: file.path,
                            size: file.size,
                            lastModified: file.last_modified || null
                        });
                    }
                }
            } catch (error) {
                // Directory doesn't exist yet, that's okay
                if (error.status !== 404) {
                    console.error(`Error reading reviews from ${path}:`, error);
                }
            }
        }
        
        return reviews;
    }
    
    formatReviewContent(reviewData) {
        const { reviewType, score, isPositive, content, metadata = {} } = reviewData;
        
        return `# ${reviewType} Review

**Reviewer**: ${reviewData.reviewerUsername}
**Date**: ${new Date().toISOString().split('T')[0]}
**Type**: ${reviewData.automated ? 'Automated' : 'Manual'}
**Score**: ${score}/1.0
**Decision**: ${isPositive ? 'POSITIVE' : 'NEGATIVE'}

## Review Content

${content}

## Metadata

${Object.entries(metadata).map(([key, value]) => `- **${key}**: ${value}`).join('\n')}

---
*Review submitted via llmXive v2.0 review system*
`;
    }
    
    async updateProjectReviews(projectId, artifactType, reviewInfo) {
        // Read current phases
        const phases = await this.files.readJSON(`projects/${projectId}/.llmxive/phases.json`);
        
        // Map artifact types to phases
        const phaseMap = {
            'idea': 'idea',
            'technical-design': 'technical_design', 
            'implementation-plan': 'implementation_plan',
            'code': 'implementation',
            'data': 'implementation',
            'paper': 'paper'
        };
        
        const phaseName = phaseMap[artifactType];
        if (!phaseName || !phases[phaseName]) {
            throw new Error(`Unknown artifact type: ${artifactType}`);
        }
        
        const phase = phases[phaseName];
        
        // Update review tracking
        if (!phase.reviews) {
            phase.reviews = {
                required_points: 0,
                current_points: 0,
                automated_reviews: 0,
                manual_reviews: 0,
                review_files: []
            };
        }
        
        // Add review file
        phase.reviews.review_files.push(reviewInfo.path);
        
        // Update counters
        if (reviewInfo.automated) {
            phase.reviews.automated_reviews++;
        } else {
            phase.reviews.manual_reviews++;
        }
        
        // Update points if positive review
        if (reviewInfo.isPositive) {
            phase.reviews.current_points += reviewInfo.points;
        }
        
        // Save updated phases
        await this.files.writeJSON(
            `projects/${projectId}/.llmxive/phases.json`,
            phases,
            `Update review tracking for ${projectId} ${artifactType}`
        );
    }
    
    async checkPhaseAdvancement(projectId, artifactType) {
        // Read project configuration
        const [phases, dependencies] = await Promise.all([
            this.files.readJSON(`projects/${projectId}/.llmxive/phases.json`),
            this.files.readJSON(`projects/${projectId}/.llmxive/dependencies.json`)
        ]);
        
        // Check if any phase can now advance based on review points
        for (const [phaseName, phase] of Object.entries(phases)) {
            if (phase.status === 'pending' || phase.status === 'blocked') {
                const canAdvance = await this.canPhaseAdvance(phaseName, phases, dependencies);
                if (canAdvance) {
                    phase.status = 'ready';
                    await this.files.writeJSON(
                        `projects/${projectId}/.llmxive/phases.json`,
                        phases,
                        `Phase ${phaseName} now ready for ${projectId}`
                    );
                    
                    // Log phase advancement
                    await this.files.appendToLog('.llmxive-system/logs/orchestrator/phase-changes.json', {
                        event: 'phase_ready',
                        projectId: projectId,
                        phase: phaseName,
                        trigger: 'review_completion'
                    });
                }
            }
        }
    }
    
    async canPhaseAdvance(phaseName, phases, dependencies) {
        const phase = phases[phaseName];
        const phaseDepends = dependencies.phase_dependencies[phaseName];
        
        if (!phaseDepends) return true; // No dependencies
        
        // Check phase dependencies
        if (phaseDepends.depends_on_phases) {
            for (const depPhaseName of phaseDepends.depends_on_phases) {
                const depPhase = phases[depPhaseName];
                if (!depPhase || depPhase.status !== 'completed') {
                    return false;
                }
            }
        }
        
        // Check quality gates
        if (phaseDepends.quality_gates) {
            for (const [gateName, gate] of Object.entries(phaseDepends.quality_gates)) {
                if (gate.type === 'review_points') {
                    if (gate.current_value < gate.minimum_value) {
                        return false;
                    }
                }
            }
        }
        
        return true;
    }
}
```

## Unified Model Management

### **JSON-Based Model Registry**

#### `.llmxive-system/registry/models.json`
```json
{
  "claude-4-sonnet": {
    "id": "claude-4-sonnet",
    "name": "Claude 4 Sonnet", 
    "provider": "anthropic",
    "family": "claude-4",
    "version": "2024-11-20",
    "status": "active",
    "capabilities": {
      "context_length": 200000,
      "max_output_tokens": 8192,
      "supports_multimodal": true,
      "supports_code": true,
      "supports_function_calling": true,
      "reasoning": "expert",
      "technical_writing": "expert", 
      "code_generation": "advanced",
      "data_analysis": "advanced",
      "scientific_writing": "expert"
    },
    "requirements": {
      "api_key": true,
      "internet": true,
      "min_ram_gb": 0,
      "min_storage_gb": 0,
      "gpu_required": false
    },
    "performance": {
      "tokens_per_second": 50,
      "latency_ms": 1500,
      "cost_per_1k_input": 0.003,
      "cost_per_1k_output": 0.015
    }
  },
  "gpt-4o": {
    "id": "gpt-4o",
    "name": "GPT-4 Omni",
    "provider": "openai", 
    "family": "gpt-4",
    "version": "2024-08-06",
    "status": "active",
    "capabilities": {
      "context_length": 128000,
      "max_output_tokens": 4096,
      "supports_multimodal": true,
      "supports_code": true,
      "supports_function_calling": true,
      "reasoning": "expert",
      "technical_writing": "advanced",
      "code_generation": "expert",
      "data_analysis": "expert", 
      "scientific_writing": "advanced"
    },
    "requirements": {
      "api_key": true,
      "internet": true,
      "min_ram_gb": 0,
      "min_storage_gb": 0,
      "gpu_required": false
    },
    "performance": {
      "tokens_per_second": 75,
      "latency_ms": 1200,
      "cost_per_1k_input": 0.005,
      "cost_per_1k_output": 0.015
    }
  },
  "tinyllama-1.1b-chat": {
    "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "name": "TinyLlama 1.1B Chat",
    "provider": "huggingface",
    "family": "tinyllama", 
    "version": "v1.0",
    "status": "active",
    "capabilities": {
      "context_length": 2048,
      "max_output_tokens": 512,
      "supports_multimodal": false,
      "supports_code": true,
      "supports_function_calling": false,
      "reasoning": "basic",
      "technical_writing": "intermediate",
      "code_generation": "basic", 
      "data_analysis": "basic",
      "scientific_writing": "intermediate"
    },
    "requirements": {
      "api_key": false,
      "internet": true,
      "min_ram_gb": 4.0,
      "min_storage_gb": 2.2,
      "gpu_required": false
    },
    "performance": {
      "tokens_per_second": 25,
      "latency_ms": 500,
      "cost_per_1k_input": 0.0,
      "cost_per_1k_output": 0.0
    }
  }
}
```

#### `.llmxive-system/registry/providers.json`
```json
{
  "anthropic": {
    "id": "anthropic",
    "name": "Anthropic",
    "api_base_url": "https://api.anthropic.com",
    "authentication_type": "api_key",
    "requires_internet": true,
    "rate_limits": {
      "requests_per_minute": 50,
      "tokens_per_minute": 100000
    },
    "request_format": {
      "headers": {
        "Content-Type": "application/json",
        "x-api-key": "${ANTHROPIC_API_KEY}",
        "anthropic-version": "2023-06-01"
      },
      "endpoint": "/v1/messages",
      "body_template": {
        "model": "${model_id}",
        "max_tokens": "${max_tokens}",
        "messages": [{"role": "user", "content": "${prompt}"}]
      }
    }
  },
  "openai": {
    "id": "openai", 
    "name": "OpenAI",
    "api_base_url": "https://api.openai.com",
    "authentication_type": "api_key",
    "requires_internet": true,
    "rate_limits": {
      "requests_per_minute": 60,
      "tokens_per_minute": 150000
    },
    "request_format": {
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer ${OPENAI_API_KEY}"
      },
      "endpoint": "/v1/chat/completions",
      "body_template": {
        "model": "${model_id}",
        "max_tokens": "${max_tokens}",
        "messages": [{"role": "user", "content": "${prompt}"}]
      }
    }
  },
  "huggingface": {
    "id": "huggingface",
    "name": "Hugging Face",
    "api_base_url": "https://api-inference.huggingface.co",
    "authentication_type": "api_key",
    "requires_internet": true,
    "rate_limits": {
      "requests_per_minute": 30,
      "tokens_per_minute": 50000
    },
    "request_format": {
      "headers": {
        "Authorization": "Bearer ${HUGGINGFACE_API_KEY}"
      },
      "endpoint": "/models/${model_id}",
      "body_template": {
        "inputs": "${prompt}",
        "parameters": {
          "max_new_tokens": "${max_tokens}",
          "temperature": 0.1
        }
      }
    }
  }
}
```

## Content Moderation with File-Based Storage

### **Moderation Manager**

```javascript
class ModerationManager {
    constructor(githubClient) {
        this.github = githubClient;
        this.files = githubClient.files;
        this.moderationThreshold = 0.7;
        this.autoBlockThreshold = 10;
    }
    
    async moderateContent(contentData) {
        const {
            contentType,
            contentId, 
            submitterUsername,
            contentText,
            contentUrl
        } = contentData;
        
        // Run automated moderation
        const moderationResult = await this.runAutomatedModeration(contentText);
        
        // Create moderation record
        const moderationRecord = {
            id: this.generateModerationId(),
            contentType: contentType,
            contentId: contentId,
            submitterUsername: submitterUsername,
            contentText: contentText,
            contentUrl: contentUrl,
            automatedScore: moderationResult.score,
            automatedFlags: moderationResult.flags,
            status: moderationResult.score >= this.moderationThreshold ? 'requires_review' : 'approved',
            submittedAt: new Date().toISOString(),
            reviewedAt: null,
            humanDecision: null
        };
        
        // Store moderation record
        await this.storeModerationRecord(moderationRecord);
        
        // Update user history
        await this.updateUserModerationHistory(submitterUsername, moderationRecord);
        
        // Create GitHub issue if requires review
        if (moderationRecord.status === 'requires_review') {
            await this.createModerationIssue(moderationRecord);
        }
        
        return {
            moderationId: moderationRecord.id,
            status: moderationRecord.status,
            score: moderationResult.score,
            flags: moderationResult.flags
        };
    }
    
    async storeModerationRecord(record) {
        const date = new Date().toISOString().split('T')[0];
        const filename = `moderation_${date}.json`;
        const filePath = `.llmxive-system/logs/moderation/${filename}`;
        
        // Read existing moderation log for today
        const existingLog = await this.files.readJSON(filePath) || [];
        
        // Add new record
        existingLog.push(record);
        
        // Save updated log
        await this.files.writeJSON(filePath, existingLog, `Add moderation record ${record.id}`);
    }
    
    async updateUserModerationHistory(username, moderationRecord) {
        const userHistoryPath = `.llmxive-system/registry/users.json`;
        const userHistory = await this.files.readJSON(userHistoryPath) || {};
        
        if (!userHistory[username]) {
            userHistory[username] = {
                github_username: username,
                total_submissions: 0,
                approved_submissions: 0,
                rejected_submissions: 0,
                spam_submissions: 0,
                user_status: 'active',
                consecutive_rejections: 0,
                last_rejection_at: null,
                created_at: new Date().toISOString()
            };
        }
        
        const user = userHistory[username];
        user.total_submissions++;
        
        if (moderationRecord.status === 'approved') {
            user.approved_submissions++;
            user.consecutive_rejections = 0; // Reset on approval
        } else if (moderationRecord.status === 'rejected') {
            user.rejected_submissions++;
            user.consecutive_rejections++;
            user.last_rejection_at = new Date().toISOString();
            
            // Auto-block check
            if (user.consecutive_rejections >= this.autoBlockThreshold) {
                user.user_status = 'blocked';
                user.blocked_at = new Date().toISOString();
                user.blocked_reason = 'Exceeded rejection threshold (automated)';
            }
        }
        
        if (moderationRecord.automatedFlags.includes('spam')) {
            user.spam_submissions++;
        }
        
        user.updated_at = new Date().toISOString();
        
        // Save updated user history
        await this.files.writeJSON(userHistoryPath, userHistory, `Update moderation history for ${username}`);
        
        return user;
    }
    
    generateModerationId() {
        return `mod_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    async runAutomatedModeration(content) {
        // Implementation of automated moderation algorithms
        const flags = [];
        let score = 0.0;
        
        // Spam detection
        const spamScore = this.detectSpam(content);
        if (spamScore > 0.5) {
            flags.push('spam');
            score = Math.max(score, spamScore);
        }
        
        // Add other moderation checks...
        
        return { score, flags };
    }
    
    detectSpam(content) {
        // Simple spam detection implementation
        let spamScore = 0.0;
        const text = content.toLowerCase();
        
        const spamPatterns = [
            /click here/gi,
            /free money/gi,
            /urgent.*respond/gi
        ];
        
        spamPatterns.forEach(pattern => {
            if (pattern.test(text)) {
                spamScore += 0.3;
            }
        });
        
        return Math.min(spamScore, 1.0);
    }
}
```

## Edge Case Handling

### **Comprehensive Error Recovery**

```javascript
class ErrorRecoveryManager {
    constructor(githubClient) {
        this.github = githubClient;
        this.files = githubClient.files;
        this.maxRetries = 3;
        this.backoffBase = 1000; // 1 second
    }
    
    async withRetry(operation, context = {}) {
        let lastError;
        
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error;
                
                // Log the error
                await this.logError(error, { ...context, attempt });
                
                // Check if we should retry
                if (!this.shouldRetry(error, attempt)) {
                    break;
                }
                
                // Exponential backoff
                const delay = this.backoffBase * Math.pow(2, attempt - 1);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        // All retries failed
        await this.handleFinalFailure(lastError, context);
        throw lastError;
    }
    
    shouldRetry(error, attempt) {
        if (attempt >= this.maxRetries) return false;
        
        // Retry on network errors
        if (error.name === 'NetworkError') return true;
        
        // Retry on rate limit errors
        if (error.status === 403 && error.message.includes('rate limit')) return true;
        
        // Retry on server errors
        if (error.status >= 500) return true;
        
        // Don't retry on client errors
        return false;
    }
    
    async logError(error, context) {
        const errorEntry = {
            error: {
                name: error.name,
                message: error.message,
                status: error.status,
                stack: error.stack
            },
            context: context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        try {
            await this.files.appendToLog('.llmxive-system/logs/errors/client-errors.json', errorEntry);
        } catch (logError) {
            // Fallback to console if logging fails
            console.error('Failed to log error:', logError);
            console.error('Original error:', error);
        }
    }
    
    async handleGitHubOutage() {
        // Switch to offline mode
        this.github.isOffline = true;
        
        // Show user notification
        this.showNotification('GitHub services are currently unavailable. Working in offline mode.', 'warning');
        
        // Try to use cached data
        await this.loadCachedData();
        
        // Set up periodic retry
        this.setupOutageRecovery();
    }
    
    async handleRepositoryMigration(oldLocation, newLocation) {
        // Update all project references
        const projects = await this.files.readJSON('.llmxive-system/registry/projects.json') || {};
        
        for (const [projectId, project] of Object.entries(projects)) {
            if (project.location && project.location.repository === oldLocation.repository) {
                project.location = newLocation;
            }
        }
        
        await this.files.writeJSON(
            '.llmxive-system/registry/projects.json',
            projects,
            `Migrate project references from ${oldLocation.repository} to ${newLocation.repository}`
        );
    }
    
    async handleCorruptedProjectData(projectId) {
        // Try to recover from backup
        const backup = await this.findLatestBackup(projectId);
        if (backup) {
            await this.restoreFromBackup(projectId, backup);
            return true;
        }
        
        // Try to reconstruct from git history
        const reconstructed = await this.reconstructFromGitHistory(projectId);
        if (reconstructed) {
            return true;
        }
        
        // Mark project as corrupted and require manual intervention
        await this.markProjectCorrupted(projectId);
        return false;
    }
}
```

## Implementation Timeline

### **Revised Phased Approach: 8-10 weeks**

**Phase 1: Core Infrastructure (2-3 weeks)**
- Unified GitHub client with file-based persistence
- Basic project structure and template integration
- Authentication and security framework

**Phase 2: Review System (2 weeks)**  
- Consistent review structure across all artifacts
- Review submission and tracking system
- Quality gate checking and phase advancement

**Phase 3: Content Management (2 weeks)**
- Model registry and provider system
- Content moderation with file-based storage
- Template initialization and customization

**Phase 4: Error Handling & Edge Cases (1-2 weeks)**
- Comprehensive error recovery
- Offline mode and caching
- Edge case handling and fallbacks

**Phase 5: Testing & Optimization (1-2 weeks)**
- End-to-end testing
- Performance optimization
- Production deployment

## Conclusion

This consolidated design resolves all architectural inconsistencies identified in the technical review while maintaining the full functionality required for automated scientific discovery. The file-based persistence strategy works within GitHub Pages constraints while providing all necessary features including:

- ✅ Professional LaTeX template integration
- ✅ Comprehensive review system for all artifacts  
- ✅ Multi-model support with provider flexibility
- ✅ Content moderation with human oversight
- ✅ Git submodule handling for large projects
- ✅ Robust error handling and edge case management
- ✅ Complete GitHub Pages compatibility

The design is now **implementation-ready** with a clear, consistent architecture that addresses all requirements while remaining feasible within the constraints of free GitHub hosting.