# llmXive v2.0: GitHub-Based Web Architecture

**Project ID**: LLMX-2024-001-WEB  
**Date**: 2025-07-06  
**Status**: Design Phase - GitHub-Focused  
**Contributors**: Claude (Sonnet 4), Jeremy Manning  

## Overview

This document outlines a completely web-based llmXive v2.0 architecture that leverages GitHub for storage, GitHub Pages for hosting, and GitHub Actions for automation. The system is designed to be freely hosted, scalable, and automatically manage project repositories as they grow.

## Core Architecture Principles

### 1. **GitHub-Native Design**
- **Primary Storage**: GitHub repositories for all project data
- **Hosting**: GitHub Pages (github.io) for the web interface
- **Automation**: GitHub Actions for all processing workflows
- **Authentication**: GitHub OAuth for user management
- **API**: GitHub REST/GraphQL APIs for all data operations

### 2. **Scalable Repository Management**
- **Small Projects**: Stored as subfolders in main repository
- **Large Projects**: Automatically split into separate repositories with git submodules
- **Threshold**: 100MB size limit triggers automatic repository creation
- **Organization**: All under ContextLab organization for unified management

### 3. **Zero-Server Architecture**
- **Static Site**: Pure client-side JavaScript application
- **No Backend**: All operations through GitHub APIs
- **No Database**: GitHub repositories serve as the database
- **No Infrastructure Costs**: Completely free hosting and operation

## Repository Structure

### Main Repository: `llmXive`

```
llmXive/
├── docs/                           # GitHub Pages site
│   ├── index.html                 # Main application entry point
│   ├── css/
│   │   ├── app.css                # Main application styles
│   │   ├── components.css         # Component-specific styles
│   │   └── themes.css             # Theme and branding
│   ├── js/
│   │   ├── core/
│   │   │   ├── app.js             # Main application controller
│   │   │   ├── github-client.js   # GitHub API wrapper
│   │   │   ├── project-manager.js # Project management logic
│   │   │   ├── dependency-resolver.js # Client-side dependency resolution
│   │   │   └── repository-manager.js  # Repository split/merge logic
│   │   ├── components/
│   │   │   ├── project-browser.js # Project browsing interface
│   │   │   ├── task-manager.js    # Task management UI
│   │   │   ├── review-system.js   # Review submission and display
│   │   │   ├── model-selector.js  # Model selection interface
│   │   │   └── dependency-viewer.js # Dependency visualization
│   │   ├── workers/
│   │   │   ├── orchestrator.js    # Background task orchestration
│   │   │   ├── file-processor.js  # File processing worker
│   │   │   └── sync-manager.js    # Repository synchronization
│   │   └── utils/
│   │       ├── markdown-parser.js # Markdown processing
│   │       ├── validation.js      # Input validation
│   │       └── cache-manager.js   # Browser cache management
│   └── config/
│       ├── pipeline-stages.json   # Pipeline configuration
│       ├── model-registry.json    # Available models
│       └── task-definitions.json  # Task type definitions
├── projects/                      # Small projects (< 100MB)
│   ├── PROJ-001-example/
│   │   ├── .project-config.json   # Project metadata
│   │   ├── idea/
│   │   │   └── initial-idea.md
│   │   ├── technical-design/
│   │   │   ├── main.md
│   │   │   └── diagrams/
│   │   ├── implementation-plan/
│   │   │   └── plan.md
│   │   ├── code/
│   │   │   ├── src/
│   │   │   ├── tests/
│   │   │   └── notebooks/
│   │   ├── data/
│   │   │   ├── raw/
│   │   │   └── processed/
│   │   ├── papers/
│   │   │   ├── draft.tex
│   │   │   └── figures/
│   │   └── reviews/
│   │       ├── design/
│   │       ├── implementation/
│   │       └── paper/
│   └── PROJ-002-another/
├── submodules/                    # Large projects (> 100MB)
│   ├── PROJ-003-large-project/   # Git submodule -> separate repo
│   └── PROJ-004-huge-dataset/    # Git submodule -> separate repo
├── .github/
│   ├── workflows/
│   │   ├── orchestrator.yml       # Main orchestration workflow
│   │   ├── project-split.yml      # Automatic repository splitting
│   │   ├── dependency-check.yml   # Dependency validation
│   │   ├── review-automation.yml  # Automated review processing
│   │   └── site-deployment.yml    # GitHub Pages deployment
│   └── templates/
│       ├── project-template/      # Template for new projects
│       └── repository-template/   # Template for split repositories
├── orchestrator/
│   ├── task-definitions/          # Task definition .md files
│   │   ├── idea-generation.md
│   │   ├── technical-design.md
│   │   ├── implementation-planning.md
│   │   ├── code-implementation.md
│   │   ├── paper-writing.md
│   │   └── review-tasks.md
│   ├── models/
│   │   ├── registry/              # Model registry .md files
│   │   │   ├── claude-3.5-sonnet.md
│   │   │   ├── gpt-4o.md
│   │   │   └── local-models/
│   │   └── personalities/         # Personality .md files
│   │       ├── technical-architect.md
│   │       ├── scientific-researcher.md
│   │       └── domain-experts/
│   └── pipeline/
│       ├── dependency-rules.json  # Dependency configuration
│       ├── quality-gates.json     # Quality gate definitions
│       └── automation-config.json # Automation settings
├── scripts/
│   ├── setup-new-project.js      # Project initialization
│   ├── split-large-project.js    # Repository splitting logic
│   ├── sync-submodules.js         # Submodule synchronization
│   └── validate-dependencies.js  # Dependency validation
└── README.md
```

### Large Project Repository: `llmXive-PROJ-XXX`

```
llmXive-PROJ-003-large-project/
├── .project-config.json          # Project metadata (links back to main repo)
├── idea/
├── technical-design/
├── implementation-plan/
├── code/                          # Large codebase
│   ├── src/                      # >50MB of source code
│   ├── models/                   # Large ML models
│   └── experiments/              # Extensive experimental code
├── data/                         # Large datasets
│   ├── raw/                      # >100MB datasets
│   ├── processed/                # Processed data
│   └── synthetic/               # Generated datasets
├── papers/
├── reviews/
├── .github/
│   └── workflows/
│       ├── sync-to-main.yml      # Sync metadata back to main repo
│       ├── project-ci.yml        # Project-specific CI/CD
│       └── data-processing.yml   # Data processing workflows
└── README.md                     # Project-specific README
```

## Core Components

### 1. GitHub Pages Application

#### Main Application (`docs/js/core/app.js`)

```javascript
class LlmXiveApp {
    constructor() {
        this.githubClient = new GitHubClient();
        this.projectManager = new ProjectManager(this.githubClient);
        this.dependencyResolver = new DependencyResolver();
        this.repositoryManager = new RepositoryManager(this.githubClient);
        
        this.currentUser = null;
        this.projects = new Map();
        this.cache = new CacheManager();
    }
    
    async initialize() {
        // Initialize GitHub authentication
        await this.githubClient.authenticate();
        this.currentUser = await this.githubClient.getCurrentUser();
        
        // Load project registry
        await this.loadProjectRegistry();
        
        // Initialize UI components
        this.initializeComponents();
        
        // Start background orchestration
        this.startBackgroundOrchestration();
    }
    
    async loadProjectRegistry() {
        // Load projects from main repository
        const localProjects = await this.projectManager.loadLocalProjects();
        
        // Load projects from submodules
        const submoduleProjects = await this.projectManager.loadSubmoduleProjects();
        
        // Merge and cache project registry
        const allProjects = [...localProjects, ...submoduleProjects];
        this.projects = new Map(allProjects.map(p => [p.id, p]));
        
        // Update cache
        await this.cache.set('project-registry', Array.from(this.projects.values()));
    }
    
    async createNewProject(projectData) {
        const projectId = this.generateProjectId();
        
        // Create project structure
        const project = await this.projectManager.createProject(projectId, projectData);
        
        // Add to registry
        this.projects.set(projectId, project);
        
        // Start with local storage (will auto-split if it grows large)
        await this.projectManager.initializeLocalProject(project);
        
        // Update UI
        this.refreshProjectList();
        
        return project;
    }
    
    startBackgroundOrchestration() {
        // Use Web Workers for background processing
        if (typeof Worker !== 'undefined') {
            this.orchestratorWorker = new Worker('/js/workers/orchestrator.js');
            this.orchestratorWorker.postMessage({
                type: 'initialize',
                projects: Array.from(this.projects.values())
            });
            
            this.orchestratorWorker.onmessage = (e) => {
                this.handleOrchestratorMessage(e.data);
            };
        }
    }
}
```

#### GitHub API Client (`docs/js/core/github-client.js`)

```javascript
class GitHubClient {
    constructor() {
        this.baseUrl = 'https://api.github.com';
        this.token = null;
        this.rateLimitRemaining = 5000;
        this.rateLimitReset = null;
    }
    
    async authenticate() {
        // Try to get token from localStorage first
        this.token = localStorage.getItem('github-token');
        
        if (!this.token) {
            // Initiate GitHub OAuth flow
            await this.initiateOAuthFlow();
        }
        
        // Validate token
        try {
            await this.getCurrentUser();
        } catch (error) {
            // Token invalid, re-authenticate
            localStorage.removeItem('github-token');
            await this.initiateOAuthFlow();
        }
    }
    
    async initiateOAuthFlow() {
        // GitHub OAuth flow for client-side apps
        const clientId = 'your-github-app-client-id';
        const redirectUri = `${window.location.origin}/auth-callback.html`;
        const scope = 'repo,user:email,read:org';
        
        const authUrl = `https://github.com/login/oauth/authorize?` +
            `client_id=${clientId}&` +
            `redirect_uri=${encodeURIComponent(redirectUri)}&` +
            `scope=${encodeURIComponent(scope)}&` +
            `state=${this.generateState()}`;
        
        // Open OAuth popup
        const popup = window.open(authUrl, 'github-auth', 'width=600,height=600');
        
        return new Promise((resolve, reject) => {
            const messageHandler = (event) => {
                if (event.origin !== window.location.origin) return;
                
                if (event.data.type === 'github-auth-success') {
                    this.token = event.data.token;
                    localStorage.setItem('github-token', this.token);
                    window.removeEventListener('message', messageHandler);
                    popup.close();
                    resolve();
                } else if (event.data.type === 'github-auth-error') {
                    window.removeEventListener('message', messageHandler);
                    popup.close();
                    reject(new Error(event.data.error));
                }
            };
            
            window.addEventListener('message', messageHandler);
        });
    }
    
    async apiRequest(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Authorization': `token ${this.token}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        const config = {
            ...options,
            headers
        };
        
        const response = await fetch(url, config);
        
        // Update rate limit info
        this.rateLimitRemaining = parseInt(response.headers.get('X-RateLimit-Remaining'));
        this.rateLimitReset = new Date(response.headers.get('X-RateLimit-Reset') * 1000);
        
        if (!response.ok) {
            throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
        }
        
        return response.json();
    }
    
    async getRepositoryContent(owner, repo, path) {
        return this.apiRequest(`/repos/${owner}/${repo}/contents/${path}`);
    }
    
    async createFile(owner, repo, path, content, message, branch = 'main') {
        return this.apiRequest(`/repos/${owner}/${repo}/contents/${path}`, {
            method: 'PUT',
            body: JSON.stringify({
                message,
                content: btoa(unescape(encodeURIComponent(content))), // Base64 encode
                branch
            })
        });
    }
    
    async updateFile(owner, repo, path, content, message, sha, branch = 'main') {
        return this.apiRequest(`/repos/${owner}/${repo}/contents/${path}`, {
            method: 'PUT',
            body: JSON.stringify({
                message,
                content: btoa(unescape(encodeURIComponent(content))),
                sha,
                branch
            })
        });
    }
    
    async createRepository(name, description, isPrivate = false) {
        return this.apiRequest('/repos', {
            method: 'POST',
            body: JSON.stringify({
                name,
                description,
                private: isPrivate,
                auto_init: true,
                has_issues: true,
                has_projects: true,
                has_wiki: false
            })
        });
    }
    
    async createOrganizationRepository(org, name, description, isPrivate = false) {
        return this.apiRequest(`/orgs/${org}/repos`, {
            method: 'POST',
            body: JSON.stringify({
                name,
                description,
                private: isPrivate,
                auto_init: true,
                has_issues: true,
                has_projects: true,
                has_wiki: false
            })
        });
    }
    
    async addSubmodule(owner, repo, submodulePath, submoduleUrl, branch = 'main') {
        // Add submodule via .gitmodules file update
        const gitmodulesPath = '.gitmodules';
        
        try {
            // Get existing .gitmodules
            const existing = await this.getRepositoryContent(owner, repo, gitmodulesPath);
            const existingContent = atob(existing.content);
            
            const newSubmodule = `
[submodule "${submodulePath}"]
    path = ${submodulePath}
    url = ${submoduleUrl}
    branch = ${branch}`;
            
            const newContent = existingContent + newSubmodule;
            
            await this.updateFile(
                owner, repo, gitmodulesPath, newContent,
                `Add submodule ${submodulePath}`, existing.sha, branch
            );
        } catch (error) {
            // .gitmodules doesn't exist, create it
            const content = `[submodule "${submodulePath}"]
    path = ${submodulePath}
    url = ${submoduleUrl}
    branch = ${branch}`;
            
            await this.createFile(
                owner, repo, gitmodulesPath, content,
                `Add submodule ${submodulePath}`, branch
            );
        }
    }
}
```

#### Repository Manager (`docs/js/core/repository-manager.js`)

```javascript
class RepositoryManager {
    constructor(githubClient) {
        this.github = githubClient;
        this.organization = 'ContextLab';
        this.mainRepo = 'llmXive';
        this.sizeThreshold = 100 * 1024 * 1024; // 100MB
    }
    
    async checkProjectSize(projectId) {
        const projectPath = `projects/${projectId}`;
        
        try {
            const contents = await this.getDirectorySize(
                this.organization, this.mainRepo, projectPath
            );
            return contents.totalSize;
        } catch (error) {
            console.error(`Error checking project size for ${projectId}:`, error);
            return 0;
        }
    }
    
    async getDirectorySize(owner, repo, path) {
        const contents = await this.github.getRepositoryContent(owner, repo, path);
        let totalSize = 0;
        const files = [];
        
        for (const item of contents) {
            if (item.type === 'file') {
                totalSize += item.size;
                files.push(item);
            } else if (item.type === 'dir') {
                const subDir = await this.getDirectorySize(owner, repo, item.path);
                totalSize += subDir.totalSize;
                files.push(...subDir.files);
            }
        }
        
        return { totalSize, files };
    }
    
    async splitLargeProject(projectId) {
        console.log(`Splitting large project: ${projectId}`);
        
        // 1. Create new repository
        const newRepoName = `llmXive-${projectId}`;
        const newRepo = await this.github.createOrganizationRepository(
            this.organization,
            newRepoName,
            `llmXive project: ${projectId}`,
            false // public repository
        );
        
        // 2. Copy project files to new repository
        await this.copyProjectToNewRepository(projectId, newRepo.full_name);
        
        // 3. Add as submodule to main repository
        const submodulePath = `submodules/${projectId}`;
        await this.github.addSubmodule(
            this.organization,
            this.mainRepo,
            submodulePath,
            newRepo.clone_url
        );
        
        // 4. Update project registry
        await this.updateProjectRegistry(projectId, {
            location: 'submodule',
            repository: newRepo.full_name,
            submodulePath: submodulePath
        });
        
        // 5. Remove from main repository (keep metadata)
        await this.removeProjectFromMain(projectId);
        
        console.log(`Project ${projectId} successfully split to ${newRepo.full_name}`);
        return newRepo;
    }
    
    async copyProjectToNewRepository(projectId, targetRepo) {
        const [owner, repo] = targetRepo.split('/');
        const sourcePath = `projects/${projectId}`;
        
        // Get all files from source project
        const projectData = await this.getDirectorySize(
            this.organization, this.mainRepo, sourcePath
        );
        
        // Copy each file to new repository
        for (const file of projectData.files) {
            try {
                // Get file content from main repo
                const fileData = await this.github.getRepositoryContent(
                    this.organization, this.mainRepo, file.path
                );
                
                // Calculate new path (remove projects/projectId prefix)
                const newPath = file.path.replace(`projects/${projectId}/`, '');
                
                // Create file in new repository
                await this.github.createFile(
                    owner, repo, newPath,
                    atob(fileData.content),
                    `Copy ${newPath} from main repository`
                );
                
                // Add small delay to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 100));
                
            } catch (error) {
                console.error(`Error copying file ${file.path}:`, error);
            }
        }
        
        // Update project config to reference main repository
        const projectConfig = {
            projectId: projectId,
            mainRepository: `${this.organization}/${this.mainRepo}`,
            splitDate: new Date().toISOString(),
            originalPath: sourcePath
        };
        
        await this.github.createFile(
            owner, repo, '.project-config.json',
            JSON.stringify(projectConfig, null, 2),
            'Add project configuration'
        );
    }
    
    async updateProjectRegistry(projectId, updateData) {
        const registryPath = 'docs/config/project-registry.json';
        
        try {
            // Get current registry
            const registryFile = await this.github.getRepositoryContent(
                this.organization, this.mainRepo, registryPath
            );
            const registry = JSON.parse(atob(registryFile.content));
            
            // Update project entry
            const projectIndex = registry.findIndex(p => p.id === projectId);
            if (projectIndex !== -1) {
                registry[projectIndex] = { ...registry[projectIndex], ...updateData };
            }
            
            // Save updated registry
            await this.github.updateFile(
                this.organization, this.mainRepo, registryPath,
                JSON.stringify(registry, null, 2),
                `Update registry for project ${projectId}`,
                registryFile.sha
            );
            
        } catch (error) {
            console.error('Error updating project registry:', error);
        }
    }
    
    async removeProjectFromMain(projectId) {
        // Note: GitHub API doesn't support directory deletion
        // This would need to be handled by a GitHub Action
        // that can use git commands to remove the directory
        
        // Trigger GitHub Action for cleanup
        await this.github.apiRequest(
            `/repos/${this.organization}/${this.mainRepo}/dispatches`,
            {
                method: 'POST',
                body: JSON.stringify({
                    event_type: 'cleanup-split-project',
                    client_payload: {
                        projectId: projectId,
                        projectPath: `projects/${projectId}`
                    }
                })
            }
        );
    }
    
    async monitorProjectSizes() {
        // Get all local projects
        const projectsDir = await this.github.getRepositoryContent(
            this.organization, this.mainRepo, 'projects'
        );
        
        for (const project of projectsDir) {
            if (project.type === 'dir') {
                const projectId = project.name;
                const size = await this.checkProjectSize(projectId);
                
                if (size > this.sizeThreshold) {
                    console.log(`Project ${projectId} exceeds size threshold (${size} bytes)`);
                    await this.splitLargeProject(projectId);
                }
            }
        }
    }
}
```

### 2. GitHub Actions Workflows

#### Main Orchestrator (`.github/workflows/orchestrator.yml`)

```yaml
name: llmXive Orchestrator

on:
  schedule:
    - cron: '*/15 * * * *'  # Run every 15 minutes
  workflow_dispatch:
    inputs:
      force_execution:
        description: 'Force execution of all ready tasks'
        required: false
        type: boolean
        default: false

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: recursive
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: |
          npm install
          npm install -g @actions/core @actions/github
      
      - name: Load project registry
        id: load-projects
        run: |
          node scripts/load-project-registry.js
      
      - name: Check dependencies
        id: check-deps
        run: |
          node scripts/check-dependencies.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PROJECT_REGISTRY: ${{ steps.load-projects.outputs.projects }}
      
      - name: Execute ready tasks
        if: steps.check-deps.outputs.ready-tasks != ''
        run: |
          node scripts/execute-tasks.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          READY_TASKS: ${{ steps.check-deps.outputs.ready-tasks }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      
      - name: Update project statuses
        run: |
          node scripts/update-project-status.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Monitor repository sizes
        run: |
          node scripts/monitor-repo-sizes.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Commit and push changes
        if: steps.check-deps.outputs.changes-made == 'true'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "llmXive Orchestrator"
          git add .
          git commit -m "🤖 Orchestrator: Update project statuses and artifacts" || exit 0
          git push
```

#### Project Splitting (`.github/workflows/project-split.yml`)

```yaml
name: Split Large Project

on:
  repository_dispatch:
    types: [cleanup-split-project]

jobs:
  split-project:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.ADMIN_TOKEN }}  # Need admin token for submodule operations
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Remove project directory
        run: |
          PROJECT_PATH="${{ github.event.client_payload.projectPath }}"
          if [ -d "$PROJECT_PATH" ]; then
            git rm -r "$PROJECT_PATH"
            git config --local user.email "action@github.com"
            git config --local user.name "llmXive Repository Manager"
            git commit -m "🔄 Remove project after splitting to separate repository"
            git push
          fi
      
      - name: Update submodules
        run: |
          git submodule update --init --recursive
          git submodule foreach git pull origin main
          
          if [ -n "$(git status --porcelain)" ]; then
            git add .
            git commit -m "🔄 Update submodules after project split"
            git push
          fi
```

#### Dependency Checking (`.github/workflows/dependency-check.yml`)

```yaml
name: Dependency Validation

on:
  push:
    paths:
      - 'projects/**'
      - 'submodules/**'
      - 'orchestrator/**'
  pull_request:
    paths:
      - 'projects/**'
      - 'submodules/**'
      - 'orchestrator/**'

jobs:
  validate-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Validate project dependencies
        run: |
          node scripts/validate-dependencies.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Check for circular dependencies
        run: |
          node scripts/check-circular-deps.js
      
      - name: Validate project structure
        run: |
          node scripts/validate-structure.js
      
      - name: Comment on PR with validation results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            if (fs.existsSync('validation-results.json')) {
              const results = JSON.parse(fs.readFileSync('validation-results.json', 'utf8'));
              
              const comment = `## 🔍 Dependency Validation Results
              
              ${results.isValid ? '✅ All validations passed!' : '❌ Validation issues found:'}
              
              ${results.errors.map(error => `- ❌ ${error}`).join('\n')}
              ${results.warnings.map(warning => `- ⚠️ ${warning}`).join('\n')}
              
              **Projects analyzed:** ${results.projectCount}
              **Dependencies checked:** ${results.dependencyCount}`;
              
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: comment
              });
            }
```

### 3. Client-Side Dependency Resolution

#### Dependency Resolver (`docs/js/core/dependency-resolver.js`)

```javascript
class DependencyResolver {
    constructor() {
        this.dependencyGraph = new Map();
        this.pipelineStages = null;
        this.qualityGates = null;
    }
    
    async initialize() {
        // Load pipeline configuration
        this.pipelineStages = await this.loadConfig('/config/pipeline-stages.json');
        this.qualityGates = await this.loadConfig('/config/quality-gates.json');
    }
    
    async loadConfig(path) {
        const response = await fetch(path);
        return response.json();
    }
    
    buildDependencyGraph(projects) {
        this.dependencyGraph.clear();
        
        for (const project of projects) {
            const projectNode = {
                id: project.id,
                status: project.status,
                phases: project.phases || {},
                artifacts: project.artifacts || {},
                dependencies: project.dependencies || []
            };
            
            this.dependencyGraph.set(project.id, projectNode);
        }
    }
    
    getReadyTasks(projectId) {
        const project = this.dependencyGraph.get(projectId);
        if (!project) return [];
        
        const readyTasks = [];
        
        // Check each pipeline stage
        for (const [stageName, stageConfig] of Object.entries(this.pipelineStages)) {
            const phase = project.phases[stageName];
            
            if (!phase || phase.status === 'completed') continue;
            if (phase.status === 'in_progress') continue;
            
            // Check if dependencies are satisfied
            if (this.areDependenciesSatisfied(project, stageConfig)) {
                // Check quality gates
                if (this.areQualityGatesSatisfied(project, stageName)) {
                    readyTasks.push({
                        projectId: projectId,
                        taskType: stageName,
                        priority: this.calculatePriority(stageName),
                        estimatedDuration: stageConfig.estimatedDuration || 60
                    });
                }
            }
        }
        
        return readyTasks.sort((a, b) => b.priority - a.priority);
    }
    
    areDependenciesSatisfied(project, stageConfig) {
        if (!stageConfig.dependencies || stageConfig.dependencies.length === 0) {
            return true;
        }
        
        for (const dependency of stageConfig.dependencies) {
            const dependentPhase = project.phases[dependency];
            if (!dependentPhase || dependentPhase.status !== 'completed') {
                return false;
            }
        }
        
        return true;
    }
    
    areQualityGatesSatisfied(project, stageName) {
        const gates = this.qualityGates[stageName];
        if (!gates) return true;
        
        for (const [gateType, requirement] of Object.entries(gates)) {
            if (gateType === 'signed_positive_reviews') {
                const reviewPoints = this.calculateReviewPoints(project, stageName);
                if (reviewPoints < requirement) {
                    return false;
                }
            }
            
            if (gateType === 'artifact_quality') {
                const qualityScore = this.getArtifactQuality(project, stageName);
                if (qualityScore < requirement) {
                    return false;
                }
            }
        }
        
        return true;
    }
    
    calculateReviewPoints(project, stageName) {
        const reviews = project.phases[stageName]?.reviews || [];
        let points = 0;
        
        for (const review of reviews) {
            if (review.isPositive && review.isSignedOff) {
                points += review.reviewerType === 'human' ? 1.0 : 0.5;
            }
        }
        
        return points;
    }
    
    getArtifactQuality(project, stageName) {
        const artifacts = project.artifacts[stageName] || [];
        if (artifacts.length === 0) return 0;
        
        const qualityScores = artifacts
            .map(artifact => artifact.qualityScore)
            .filter(score => score !== null && score !== undefined);
        
        if (qualityScores.length === 0) return 0;
        
        return qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length;
    }
    
    calculatePriority(stageName) {
        const priorityMap = {
            'idea_generation': 10,
            'technical_design': 9,
            'design_review': 8,
            'implementation_planning': 7,
            'literature_review': 6,
            'code_implementation': 6,
            'data_generation': 6,
            'paper_writing': 5,
            'paper_review': 4
        };
        
        return priorityMap[stageName] || 1;
    }
    
    getBlockingDependencies(projectId) {
        const project = this.dependencyGraph.get(projectId);
        if (!project) return {};
        
        const blockingInfo = {};
        
        for (const [stageName, stageConfig] of Object.entries(this.pipelineStages)) {
            const phase = project.phases[stageName];
            
            if (!phase || phase.status === 'completed') continue;
            
            const blocking = [];
            
            // Check dependencies
            if (stageConfig.dependencies) {
                for (const dependency of stageConfig.dependencies) {
                    const depPhase = project.phases[dependency];
                    if (!depPhase || depPhase.status !== 'completed') {
                        blocking.push({
                            type: 'dependency',
                            requirement: dependency,
                            status: depPhase?.status || 'not_started'
                        });
                    }
                }
            }
            
            // Check quality gates
            const gates = this.qualityGates[stageName];
            if (gates) {
                for (const [gateType, requirement] of Object.entries(gates)) {
                    if (gateType === 'signed_positive_reviews') {
                        const currentPoints = this.calculateReviewPoints(project, stageName);
                        if (currentPoints < requirement) {
                            blocking.push({
                                type: 'quality_gate',
                                requirement: `${requirement} review points`,
                                current: currentPoints
                            });
                        }
                    }
                }
            }
            
            if (blocking.length > 0) {
                blockingInfo[stageName] = blocking;
            }
        }
        
        return blockingInfo;
    }
    
    validateProjectStructure(project) {
        const errors = [];
        const warnings = [];
        
        // Check required project structure
        const requiredFolders = ['idea', 'technical-design', 'implementation-plan', 'papers', 'reviews'];
        for (const folder of requiredFolders) {
            if (!project.structure || !project.structure.includes(folder)) {
                warnings.push(`Missing recommended folder: ${folder}`);
            }
        }
        
        // Check for circular dependencies
        if (this.hasCircularDependencies(project)) {
            errors.push('Circular dependencies detected');
        }
        
        // Check project ID format
        if (!/^PROJ-\d{3}-[a-zA-Z0-9-]+$/.test(project.id)) {
            errors.push('Invalid project ID format. Should be PROJ-XXX-name');
        }
        
        return {
            isValid: errors.length === 0,
            errors,
            warnings
        };
    }
    
    hasCircularDependencies(project) {
        // Simple cycle detection for project-level dependencies
        const visited = new Set();
        const recursionStack = new Set();
        
        const hasCycle = (projectId) => {
            if (recursionStack.has(projectId)) return true;
            if (visited.has(projectId)) return false;
            
            visited.add(projectId);
            recursionStack.add(projectId);
            
            const proj = this.dependencyGraph.get(projectId);
            if (proj && proj.dependencies) {
                for (const dep of proj.dependencies) {
                    if (hasCycle(dep.projectId)) {
                        return true;
                    }
                }
            }
            
            recursionStack.delete(projectId);
            return false;
        };
        
        return hasCycle(project.id);
    }
}
```

### 4. Configuration Files

#### Pipeline Stages (`docs/config/pipeline-stages.json`)

```json
{
  "idea_generation": {
    "dependencies": [],
    "outputs": ["initial_idea"],
    "estimatedDuration": 30,
    "parallelEligible": false,
    "requirements": {
      "anyModelOrHuman": true
    }
  },
  "technical_design": {
    "dependencies": ["idea_generation"],
    "outputs": ["technical_design_document"],
    "estimatedDuration": 240,
    "parallelEligible": false,
    "requirements": {
      "modelCapability": "technical_writing",
      "minimumContextLength": 16000
    }
  },
  "design_review": {
    "dependencies": ["technical_design"],
    "outputs": ["design_review"],
    "estimatedDuration": 60,
    "parallelEligible": true,
    "maxParallelInstances": 5,
    "requirements": {
      "reviewerQualification": "design_review_capable"
    }
  },
  "implementation_planning": {
    "dependencies": ["technical_design"],
    "outputs": ["implementation_plan"],
    "estimatedDuration": 180,
    "parallelEligible": false,
    "requirements": {
      "modelCapability": "technical_planning"
    }
  },
  "literature_review": {
    "dependencies": ["implementation_planning"],
    "outputs": ["literature_review"],
    "estimatedDuration": 120,
    "parallelEligible": true,
    "canExecuteWith": ["code_implementation", "data_generation"],
    "requirements": {
      "capability": "internet_access"
    }
  },
  "code_implementation": {
    "dependencies": ["implementation_planning"],
    "outputs": ["code_base"],
    "estimatedDuration": 300,
    "parallelEligible": true,
    "canExecuteWith": ["literature_review", "data_generation"],
    "requirements": {
      "modelCapability": "code_generation"
    }
  },
  "paper_writing": {
    "dependencies": ["implementation_planning", "literature_review"],
    "optionalDependencies": ["code_implementation", "statistical_analysis"],
    "outputs": ["research_paper"],
    "estimatedDuration": 240,
    "parallelEligible": false,
    "requirements": {
      "modelCapability": "scientific_writing"
    }
  }
}
```

#### Quality Gates (`docs/config/quality-gates.json`)

```json
{
  "implementation_planning": {
    "signed_positive_reviews": 5.0,
    "review_scoring": {
      "llm_positive_review": 0.5,
      "human_positive_review": 1.0
    }
  },
  "code_implementation": {
    "artifact_quality": 0.8,
    "test_coverage": 0.7
  },
  "paper_writing": {
    "artifact_quality": 0.85
  },
  "project_completion": {
    "signed_positive_reviews": 5.0,
    "overall_quality": 0.9
  }
}
```

### 5. GitHub Pages Deployment

#### Site Deployment (`.github/workflows/site-deployment.yml`)

```yaml
name: Deploy GitHub Pages

on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - 'projects/**'
      - 'submodules/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Generate project registry
        run: |
          node scripts/generate-project-registry.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build site data
        run: |
          node scripts/build-site-data.js
      
      - name: Setup Pages
        uses: actions/configure-pages@v3
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: 'docs'

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

## Benefits of This Architecture

### 1. **Zero Infrastructure Costs**
- Completely hosted on GitHub (free for public repositories)
- No servers, databases, or cloud services required
- Scales automatically with GitHub's infrastructure

### 2. **Simple Maintenance**
- Pure git-based operations
- No database schema migrations
- Version controlled configuration
- Easy rollback and recovery

### 3. **Transparent and Open**
- All operations visible in git history
- Public development process
- Community contributions welcome
- Full audit trail of all changes

### 4. **Scalable Architecture**
- Automatic repository splitting for large projects
- Git submodules for organized scaling
- Client-side processing reduces server load
- GitHub Actions for distributed processing

### 5. **Developer Friendly**
- Standard web technologies (HTML, CSS, JavaScript)
- GitHub-native workflows
- Easy local development and testing
- Standard CI/CD practices

## Implementation Roadmap

### Phase 1: Core Infrastructure (2-3 weeks)
1. Set up GitHub Pages application structure
2. Implement GitHub API client and authentication
3. Create basic project management interface
4. Set up repository monitoring and splitting logic

### Phase 2: Orchestration System (3-4 weeks)
1. Implement client-side dependency resolution
2. Create GitHub Actions workflows for automation
3. Build task execution and model integration
4. Set up review and quality gate systems

### Phase 3: Advanced Features (2-3 weeks)
1. Add advanced project visualization
2. Implement collaborative features
3. Create monitoring and analytics dashboards
4. Add comprehensive testing and validation

### Phase 4: Production Hardening (1-2 weeks)
1. Security audit and rate limiting
2. Performance optimization
3. Documentation and user guides
4. Production deployment and monitoring

## Security Considerations

### 1. **GitHub Token Management**
- OAuth flow for secure authentication
- Limited scope tokens (repo access only)
- Automatic token refresh handling
- Secure storage in browser localStorage

### 2. **Rate Limiting**
- Built-in GitHub API rate limit handling
- Intelligent request batching
- Exponential backoff for failures
- Cache to reduce API calls

### 3. **Input Validation**
- Comprehensive client-side validation
- Server-side validation via GitHub Actions
- Protection against malicious file uploads
- Sanitization of all user inputs

### 4. **Access Control**
- GitHub organization membership for write access
- Public read access for transparency
- Review requirements for sensitive operations
- Audit logging via git history

This architecture provides a scalable, maintainable, and cost-effective solution for llmXive v2.0 that leverages GitHub's robust infrastructure while maintaining the flexibility to handle projects of any size.