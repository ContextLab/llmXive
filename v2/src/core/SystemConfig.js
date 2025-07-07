/**
 * SystemConfig - Initialize and manage system configuration
 * 
 * Sets up the .llmxive-system directory structure and core configuration files
 * for the GitHub-native llmXive v2.0 architecture.
 */

class SystemConfig {
    constructor(fileManager) {
        this.fileManager = fileManager;
        this.systemPath = '.llmxive-system';
        this.initialized = false;
    }
    
    /**
     * Initialize the complete system configuration
     */
    async initialize() {
        console.log('Initializing llmXive v2.0 system configuration...');
        
        try {
            // Create system directory structure
            await this.createSystemDirectories();
            
            // Initialize core configuration files
            await this.initializeConfigFiles();
            
            // Initialize registry files
            await this.initializeRegistryFiles();
            
            // Initialize pipeline configuration
            await this.initializePipelineConfig();
            
            this.initialized = true;
            console.log('System configuration initialized successfully');
            
            return true;
            
        } catch (error) {
            console.error('Failed to initialize system configuration:', error);
            throw error;
        }
    }
    
    /**
     * Create system directory structure
     */
    async createSystemDirectories() {
        const directories = [
            `${this.systemPath}`,
            `${this.systemPath}/registry`,
            `${this.systemPath}/config`,
            `${this.systemPath}/logs`,
            `${this.systemPath}/cache`,
            `${this.systemPath}/workflows`,
            `${this.systemPath}/templates`
        ];
        
        for (const dir of directories) {
            await this.fileManager.createDirectory(dir);
        }
    }
    
    /**
     * Initialize core configuration files
     */
    async initializeConfigFiles() {
        // System configuration
        const systemConfig = {
            version: "2.0.0",
            initialized: new Date().toISOString(),
            github: {
                owner: this.fileManager.owner,
                repo: this.fileManager.repo,
                branch: this.fileManager.branch
            },
            features: {
                caching: true,
                rate_limiting: true,
                content_moderation: true,
                automated_reviews: true,
                latex_integration: true
            },
            limits: {
                max_projects: 1000,
                max_file_size_mb: 25,
                max_cache_age_minutes: 60,
                review_points_threshold: 5
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/config/system.json`,
            systemConfig,
            'Initialize system configuration'
        );
        
        // GitHub API configuration
        const githubConfig = {
            api_version: "2022-11-28",
            rate_limits: {
                core: {
                    limit: 5000,
                    remaining: 5000,
                    reset: null
                },
                search: {
                    limit: 30,
                    remaining: 30,
                    reset: null
                }
            },
            retry_policy: {
                max_retries: 3,
                base_delay_ms: 1000,
                max_delay_ms: 30000
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/config/github.json`,
            githubConfig,
            'Initialize GitHub API configuration'
        );
        
        // Cache configuration
        const cacheConfig = {
            memory_cache: {
                max_size: 1000,
                default_ttl_minutes: 5
            },
            localStorage_cache: {
                enabled: true,
                prefix: "llmxive_v2_cache_",
                max_size_mb: 50
            },
            file_cache: {
                enabled: true,
                directory: `${this.systemPath}/cache`,
                max_age_hours: 24
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/config/cache.json`,
            cacheConfig,
            'Initialize cache configuration'
        );
    }
    
    /**
     * Initialize registry files
     */
    async initializeRegistryFiles() {
        // Projects registry
        const projectsRegistry = {
            version: "1.0",
            created: new Date().toISOString(),
            last_updated: new Date().toISOString(),
            total_projects: 0,
            projects: {},
            statistics: {
                by_status: {
                    idea: 0,
                    design: 0,
                    implementation: 0,
                    review: 0,
                    completed: 0
                },
                by_type: {
                    research: 0,
                    development: 0,
                    analysis: 0,
                    other: 0
                }
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/registry/projects.json`,
            projectsRegistry,
            'Initialize projects registry'
        );
        
        // Models registry
        const modelsRegistry = {
            version: "1.0",
            created: new Date().toISOString(),
            last_updated: new Date().toISOString(),
            total_models: 0,
            models: {
                "claude-4-sonnet": {
                    id: "claude-4-sonnet",
                    name: "Claude 4 Sonnet",
                    provider: "anthropic",
                    capabilities: ["text_generation", "code_analysis", "research", "review"],
                    context_window: 200000,
                    max_tokens: 4096,
                    cost_per_1k_tokens: {
                        input: 0.015,
                        output: 0.075
                    },
                    rate_limits: {
                        requests_per_minute: 60,
                        tokens_per_minute: 40000
                    },
                    quality_score: 0.95,
                    reliability_score: 0.98,
                    available: true
                },
                "gpt-4": {
                    id: "gpt-4",
                    name: "GPT-4",
                    provider: "openai",
                    capabilities: ["text_generation", "code_analysis", "research", "review"],
                    context_window: 8192,
                    max_tokens: 4096,
                    cost_per_1k_tokens: {
                        input: 0.03,
                        output: 0.06
                    },
                    rate_limits: {
                        requests_per_minute: 200,
                        tokens_per_minute: 40000
                    },
                    quality_score: 0.93,
                    reliability_score: 0.95,
                    available: true
                },
                "gemini-pro": {
                    id: "gemini-pro",
                    name: "Gemini Pro",
                    provider: "google",
                    capabilities: ["text_generation", "code_analysis", "research", "large_context"],
                    context_window: 1000000,
                    max_tokens: 8192,
                    cost_per_1k_tokens: {
                        input: 0.0025,
                        output: 0.0075
                    },
                    rate_limits: {
                        requests_per_minute: 60,
                        tokens_per_minute: 32000
                    },
                    quality_score: 0.90,
                    reliability_score: 0.92,
                    available: true
                }
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/registry/models.json`,
            modelsRegistry,
            'Initialize models registry'
        );
        
        // Providers registry
        const providersRegistry = {
            version: "1.0",
            created: new Date().toISOString(),
            last_updated: new Date().toISOString(),
            providers: {
                "anthropic": {
                    id: "anthropic",
                    name: "Anthropic",
                    api_base_url: "https://api.anthropic.com",
                    authentication: "api_key",
                    supported_models: ["claude-4-sonnet", "claude-3-5-sonnet", "claude-3-haiku"],
                    rate_limits: {
                        requests_per_minute: 60,
                        tokens_per_minute: 40000
                    },
                    status: "active"
                },
                "openai": {
                    id: "openai",
                    name: "OpenAI",
                    api_base_url: "https://api.openai.com",
                    authentication: "api_key",
                    supported_models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    rate_limits: {
                        requests_per_minute: 500,
                        tokens_per_minute: 160000
                    },
                    status: "active"
                },
                "google": {
                    id: "google",
                    name: "Google AI",
                    api_base_url: "https://generativelanguage.googleapis.com",
                    authentication: "api_key",
                    supported_models: ["gemini-pro", "gemini-1.5-pro"],
                    rate_limits: {
                        requests_per_minute: 60,
                        tokens_per_minute: 32000
                    },
                    status: "active"
                }
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/registry/providers.json`,
            providersRegistry,
            'Initialize providers registry'
        );
        
        // Users registry
        const usersRegistry = {
            version: "1.0",
            created: new Date().toISOString(),
            last_updated: new Date().toISOString(),
            total_users: 0,
            users: {},
            moderation: {
                blocked_users: [],
                warning_users: [],
                trusted_users: []
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/registry/users.json`,
            usersRegistry,
            'Initialize users registry'
        );
    }
    
    /**
     * Initialize pipeline configuration
     */
    async initializePipelineConfig() {
        // Pipeline stages configuration
        const pipelineStages = {
            version: "1.0",
            created: new Date().toISOString(),
            stages: {
                "idea": {
                    id: "idea",
                    name: "Project Ideation",
                    description: "Initial project concept and brainstorming",
                    required_artifacts: ["initial-idea.md"],
                    optional_artifacts: ["brainstorming/*.md"],
                    review_requirements: {
                        min_reviews: 3,
                        min_points: 2.0,
                        required_review_types: ["concept_validation", "feasibility_check"]
                    },
                    dependencies: [],
                    estimated_duration_days: 3
                },
                "design": {
                    id: "design",
                    name: "Technical Design",
                    description: "Detailed technical design and specifications",
                    required_artifacts: ["technical-design/main.md"],
                    optional_artifacts: ["technical-design/diagrams/*", "technical-design/specifications/*"],
                    review_requirements: {
                        min_reviews: 5,
                        min_points: 3.0,
                        required_review_types: ["technical_review", "architecture_review"]
                    },
                    dependencies: ["idea"],
                    estimated_duration_days: 7
                },
                "implementation_plan": {
                    id: "implementation_plan",
                    name: "Implementation Planning",
                    description: "Detailed implementation plan and milestones",
                    required_artifacts: ["implementation-plan/main.md"],
                    optional_artifacts: ["implementation-plan/milestones/*", "implementation-plan/tasks/*"],
                    review_requirements: {
                        min_reviews: 5,
                        min_points: 3.0,
                        required_review_types: ["implementation_review", "project_management_review"]
                    },
                    dependencies: ["design"],
                    estimated_duration_days: 5
                },
                "implementation": {
                    id: "implementation",
                    name: "Implementation",
                    description: "Code implementation and data analysis",
                    required_artifacts: ["code/src/*", "data/processed/*"],
                    optional_artifacts: ["code/notebooks/*", "code/experiments/*"],
                    review_requirements: {
                        min_reviews: 8,
                        min_points: 5.0,
                        required_review_types: ["code_review", "data_review", "testing_review"]
                    },
                    dependencies: ["implementation_plan"],
                    estimated_duration_days: 21
                },
                "paper": {
                    id: "paper",
                    name: "Paper Writing",
                    description: "Research paper composition and documentation",
                    required_artifacts: ["paper/main.tex", "paper/bibliography.bib"],
                    optional_artifacts: ["paper/figures/*", "paper/tables/*", "paper/supplements/*"],
                    review_requirements: {
                        min_reviews: 10,
                        min_points: 7.0,
                        required_review_types: ["paper_review", "methodology_review", "writing_review"]
                    },
                    dependencies: ["implementation"],
                    estimated_duration_days: 14
                },
                "review": {
                    id: "review",
                    name: "Final Review",
                    description: "Comprehensive project review and validation",
                    required_artifacts: ["reviews/final/*"],
                    optional_artifacts: [],
                    review_requirements: {
                        min_reviews: 15,
                        min_points: 10.0,
                        required_review_types: ["comprehensive_review", "reproducibility_review"]
                    },
                    dependencies: ["paper"],
                    estimated_duration_days: 7
                }
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/registry/pipeline-stages.json`,
            pipelineStages,
            'Initialize pipeline stages configuration'
        );
        
        // Review types configuration
        const reviewTypes = {
            version: "1.0",
            created: new Date().toISOString(),
            review_types: {
                "concept_validation": {
                    id: "concept_validation",
                    name: "Concept Validation",
                    description: "Validate project concept and research questions",
                    point_value: 0.5,
                    automated: true,
                    required_models: ["claude-4-sonnet"],
                    estimated_duration_minutes: 10
                },
                "feasibility_check": {
                    id: "feasibility_check",
                    name: "Feasibility Check",
                    description: "Assess technical and resource feasibility",
                    point_value: 1.0,
                    automated: true,
                    required_models: ["gpt-4"],
                    estimated_duration_minutes: 15
                },
                "technical_review": {
                    id: "technical_review",
                    name: "Technical Review",
                    description: "Review technical design and architecture",
                    point_value: 1.0,
                    automated: true,
                    required_models: ["claude-4-sonnet", "gemini-pro"],
                    estimated_duration_minutes: 20
                },
                "code_review": {
                    id: "code_review",
                    name: "Code Review",
                    description: "Review code quality, style, and functionality",
                    point_value: 1.0,
                    automated: true,
                    required_models: ["claude-4-sonnet"],
                    estimated_duration_minutes: 30
                },
                "paper_review": {
                    id: "paper_review",
                    name: "Paper Review",
                    description: "Review research paper content and structure",
                    point_value: 1.5,
                    automated: true,
                    required_models: ["claude-4-sonnet", "gpt-4"],
                    estimated_duration_minutes: 45
                },
                "human_review": {
                    id: "human_review",
                    name: "Human Expert Review",
                    description: "Manual review by human expert",
                    point_value: 2.0,
                    automated: false,
                    required_models: [],
                    estimated_duration_minutes: 120
                }
            }
        };
        
        await this.fileManager.writeJSON(
            `${this.systemPath}/registry/review-types.json`,
            reviewTypes,
            'Initialize review types configuration'
        );
    }
    
    /**
     * Load system configuration
     */
    async loadConfig() {
        try {
            const systemConfig = await this.fileManager.readJSON(`${this.systemPath}/config/system.json`);
            const githubConfig = await this.fileManager.readJSON(`${this.systemPath}/config/github.json`);
            const cacheConfig = await this.fileManager.readJSON(`${this.systemPath}/config/cache.json`);
            
            return {
                system: systemConfig,
                github: githubConfig,
                cache: cacheConfig
            };
        } catch (error) {
            console.error('Failed to load system configuration:', error);
            throw error;
        }
    }
    
    /**
     * Load registry data
     */
    async loadRegistries() {
        try {
            const projects = await this.fileManager.readJSON(`${this.systemPath}/registry/projects.json`);
            const models = await this.fileManager.readJSON(`${this.systemPath}/registry/models.json`);
            const providers = await this.fileManager.readJSON(`${this.systemPath}/registry/providers.json`);
            const users = await this.fileManager.readJSON(`${this.systemPath}/registry/users.json`);
            const pipelineStages = await this.fileManager.readJSON(`${this.systemPath}/registry/pipeline-stages.json`);
            const reviewTypes = await this.fileManager.readJSON(`${this.systemPath}/registry/review-types.json`);
            
            return {
                projects,
                models,
                providers,
                users,
                pipelineStages,
                reviewTypes
            };
        } catch (error) {
            console.error('Failed to load registries:', error);
            throw error;
        }
    }
    
    /**
     * Check if system is initialized
     */
    async isInitialized() {
        try {
            const systemConfig = await this.fileManager.readJSON(`${this.systemPath}/config/system.json`);
            return systemConfig && systemConfig.version === "2.0.0";
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Get system status
     */
    async getStatus() {
        try {
            const config = await this.loadConfig();
            const registries = await this.loadRegistries();
            const stats = this.fileManager.getStats();
            
            return {
                initialized: this.initialized,
                version: config.system.version,
                created: config.system.initialized,
                projects: {
                    total: registries.projects.total_projects,
                    by_status: registries.projects.statistics.by_status
                },
                models: {
                    total: registries.models.total_models,
                    available: Object.values(registries.models.models).filter(m => m.available).length
                },
                file_manager: stats,
                last_check: new Date().toISOString()
            };
        } catch (error) {
            console.error('Failed to get system status:', error);
            throw error;
        }
    }
}

export default SystemConfig;