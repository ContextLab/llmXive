# llmXive v2.0: Final Design with LaTeX Template Integration

**Project ID**: LLMX-2024-001-LATEX  
**Date**: 2025-07-06  
**Status**: Design Phase - Final with LaTeX Template  
**Contributors**: Claude (Sonnet 4), Jeremy Manning  

## Overview

This document presents the final llmXive v2.0 design incorporating the ContextLab latex-base template (https://github.com/ContextLab/latex-base) as the standard structure for all research projects. This ensures consistency, reproducibility, and professional presentation across all llmXive projects.

## Enhanced Project Structure with LaTeX Template

### 1. **Standard Project Template Structure**

```
projects/PROJ-XXX-project-name/
├── .project-config.json           # llmXive project metadata
├── .gitignore                     # From latex-base template
├── .gitmodules                    # From latex-base template (if needed)
├── Dockerfile                     # From latex-base template (customized)
├── LICENSE                        # From latex-base template
├── README.md                      # Project-specific README
├── setup.sh                       # From latex-base template (customized)
│
├── idea/                          # llmXive specific: Initial project idea
│   ├── initial-idea.md
│   └── brainstorming/
│
├── technical-design/              # llmXive specific: Technical design documents
│   ├── main.md
│   ├── diagrams/
│   └── specifications/
│
├── implementation-plan/           # llmXive specific: Implementation planning
│   ├── main.md
│   ├── milestones/
│   └── tasks/
│
├── code/                          # From latex-base template
│   ├── src/                       # Source code implementation
│   ├── tests/                     # Test suite
│   ├── notebooks/                 # Jupyter notebooks for analysis
│   ├── scripts/                   # Utility scripts
│   └── experiments/               # Experimental code
│
├── data/                          # From latex-base template
│   ├── raw/                       # Raw datasets
│   ├── processed/                 # Processed datasets
│   ├── synthetic/                 # Generated datasets
│   └── external/                  # External datasets (linked/cached)
│
├── paper/                         # From latex-base template
│   ├── main.tex                   # Primary LaTeX document
│   ├── sections/                  # Paper sections
│   │   ├── abstract.tex
│   │   ├── introduction.tex
│   │   ├── methods.tex
│   │   ├── results.tex
│   │   ├── discussion.tex
│   │   └── conclusion.tex
│   ├── figures/                   # Paper figures
│   ├── tables/                    # Paper tables
│   ├── bibliography.bib           # References
│   ├── supplements/               # Supplementary materials
│   └── drafts/                    # Paper drafts and versions
│
├── reviews/                       # llmXive specific: Review system
│   ├── design/                    # Design reviews
│   │   ├── automated/
│   │   └── manual/
│   ├── implementation/            # Implementation reviews
│   │   ├── automated/
│   │   └── manual/
│   ├── paper/                     # Paper reviews
│   │   ├── automated/
│   │   └── manual/
│   └── code/                      # Code reviews
│       ├── automated/
│       └── manual/
│
└── environment/                   # llmXive specific: Environment management
    ├── docker/                    # Docker configurations
    │   ├── Dockerfile.dev         # Development environment
    │   ├── Dockerfile.prod        # Production environment
    │   └── docker-compose.yml     # Multi-service setup
    ├── conda/                     # Conda environments
    │   ├── environment.yml        # Base environment
    │   └── environment-dev.yml    # Development environment
    └── requirements/              # Python requirements
        ├── base.txt               # Base requirements
        ├── dev.txt                # Development requirements
        └── prod.txt               # Production requirements
```

### 2. **Enhanced Project Configuration**

#### Project Metadata (`.project-config.json`)

```json
{
  "project": {
    "id": "PROJ-001-neural-memory-dynamics",
    "title": "Neural Dynamics of Episodic Memory Formation",
    "description": "Investigation of neural mechanisms underlying episodic memory formation using computational models",
    "status": "in_progress",
    "priority": "high",
    "created_date": "2024-01-15",
    "last_updated": "2024-07-06",
    "estimated_completion": "2024-12-01"
  },
  "template": {
    "source": "ContextLab/latex-base",
    "version": "v1.0.0",
    "initialized_date": "2024-01-15",
    "customizations": [
      "Added llmXive-specific directories",
      "Enhanced Docker environment",
      "Integrated review system"
    ]
  },
  "contributors": [
    {
      "name": "Claude-4-Sonnet",
      "role": "primary_researcher",
      "type": "ai",
      "contributions": ["design", "implementation", "analysis"]
    },
    {
      "name": "jeremy.manning",
      "role": "supervisor",
      "type": "human",
      "contributions": ["oversight", "review", "validation"]
    }
  ],
  "phases": {
    "idea": {
      "status": "completed",
      "completed_date": "2024-01-20",
      "artifacts": ["idea/initial-idea.md"]
    },
    "technical_design": {
      "status": "completed", 
      "completed_date": "2024-02-15",
      "artifacts": ["technical-design/main.md"],
      "reviews_required": 5,
      "reviews_completed": 7
    },
    "implementation_plan": {
      "status": "completed",
      "completed_date": "2024-03-01", 
      "artifacts": ["implementation-plan/main.md"],
      "reviews_required": 5,
      "reviews_completed": 6
    },
    "implementation": {
      "status": "in_progress",
      "progress": 0.65,
      "artifacts": ["code/src/", "data/processed/", "code/experiments/"]
    },
    "paper": {
      "status": "pending",
      "artifacts": []
    },
    "review": {
      "status": "pending", 
      "artifacts": []
    }
  },
  "environment": {
    "computational_requirements": {
      "min_ram_gb": 8,
      "min_storage_gb": 50,
      "gpu_required": false,
      "docker_enabled": true
    },
    "dependencies": {
      "python_version": "3.9",
      "conda_environment": "environment/conda/environment.yml",
      "docker_image": "contextlab/cdl-python:3.9",
      "key_packages": ["brainiak", "hypertools", "matplotlib", "pandas", "seaborn"]
    }
  },
  "reproducibility": {
    "docker_image_hash": "sha256:abc123...",
    "conda_lock_file": "environment/conda/conda-lock.yml",
    "last_environment_update": "2024-07-06",
    "reproducibility_score": 0.95
  }
}
```

## Enhanced Project Initialization System

### 1. **Project Template Manager**

```javascript
class ProjectTemplateManager {
    constructor(githubClient) {
        this.github = githubClient;
        this.templateRepo = 'ContextLab/latex-base';
        this.llmxiveTemplateConfig = {
            additionalDirectories: [
                'idea',
                'technical-design', 
                'implementation-plan',
                'reviews',
                'environment'
            ],
            templateFiles: {
                'idea/initial-idea.md': this.getIdeaTemplate(),
                'technical-design/main.md': this.getTechnicalDesignTemplate(),
                'implementation-plan/main.md': this.getImplementationPlanTemplate(),
                'reviews/README.md': this.getReviewsTemplate(),
                'environment/README.md': this.getEnvironmentTemplate()
            }
        };
    }
    
    async initializeProject(projectData) {
        const { projectId, title, description, contributors } = projectData;
        
        // Step 1: Create project directory structure
        const projectPath = `projects/${projectId}`;
        
        // Step 2: Copy latex-base template files
        await this.copyLatexBaseTemplate(projectPath);
        
        // Step 3: Add llmXive-specific directories and files
        await this.addLlmXiveStructure(projectPath);
        
        // Step 4: Customize template files for this project
        await this.customizeTemplateFiles(projectPath, projectData);
        
        // Step 5: Initialize project configuration
        await this.createProjectConfig(projectPath, projectData);
        
        // Step 6: Set up computational environment
        await this.setupComputationalEnvironment(projectPath, projectData);
        
        // Step 7: Initialize git repository (if separate repo)
        if (await this.shouldCreateSeparateRepo(projectData)) {
            await this.initializeSeparateRepository(projectId, projectData);
        }
        
        return {
            projectId,
            projectPath,
            templateVersion: await this.getLatexBaseVersion(),
            initializationDate: new Date().toISOString(),
            status: 'initialized'
        };
    }
    
    async copyLatexBaseTemplate(projectPath) {
        // Get all files from latex-base template
        const templateFiles = await this.getTemplateFiles();
        
        for (const file of templateFiles) {
            if (file.type === 'file') {
                const content = await this.github.getFileContent(
                    'ContextLab', 'latex-base', file.path
                );
                
                await this.github.createFile(
                    'ContextLab', 'llmXive',
                    `${projectPath}/${file.path}`,
                    atob(content.content),
                    `Initialize ${file.path} from latex-base template`
                );
            } else if (file.type === 'dir') {
                // Create directory by adding .gitkeep file
                await this.github.createFile(
                    'ContextLab', 'llmXive',
                    `${projectPath}/${file.path}/.gitkeep`,
                    '',
                    `Create directory ${file.path}`
                );
            }
        }
    }
    
    async addLlmXiveStructure(projectPath) {
        // Create llmXive-specific directories
        for (const dir of this.llmxiveTemplateConfig.additionalDirectories) {
            await this.createDirectory(`${projectPath}/${dir}`);
            
            // Add subdirectories based on directory type
            if (dir === 'reviews') {
                const reviewTypes = ['design', 'implementation', 'paper', 'code'];
                for (const reviewType of reviewTypes) {
                    await this.createDirectory(`${projectPath}/${dir}/${reviewType}/automated`);
                    await this.createDirectory(`${projectPath}/${dir}/${reviewType}/manual`);
                }
            }
            
            if (dir === 'environment') {
                const envDirs = ['docker', 'conda', 'requirements'];
                for (const envDir of envDirs) {
                    await this.createDirectory(`${projectPath}/${dir}/${envDir}`);
                }
            }
        }
        
        // Create llmXive-specific template files
        for (const [filePath, content] of Object.entries(this.llmxiveTemplateConfig.templateFiles)) {
            await this.github.createFile(
                'ContextLab', 'llmXive',
                `${projectPath}/${filePath}`,
                content,
                `Add llmXive template file: ${filePath}`
            );
        }
    }
    
    async customizeTemplateFiles(projectPath, projectData) {
        // Customize Dockerfile with project-specific requirements
        const dockerfile = await this.generateCustomDockerfile(projectData);
        await this.updateFile(`${projectPath}/Dockerfile`, dockerfile);
        
        // Customize README.md with project information
        const readme = await this.generateCustomReadme(projectData);
        await this.updateFile(`${projectPath}/README.md`, readme);
        
        // Customize setup.sh for project-specific setup
        const setupScript = await this.generateCustomSetupScript(projectData);
        await this.updateFile(`${projectPath}/setup.sh`, setupScript);
        
        // Create conda environment file
        const condaEnv = await this.generateCondaEnvironment(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/environment/conda/environment.yml`,
            condaEnv,
            'Add conda environment configuration'
        );
    }
    
    async generateCustomDockerfile(projectData) {
        const baseDockerfile = await this.getLatexBaseDockerfile();
        
        // Customize based on project requirements
        let customDockerfile = baseDockerfile;
        
        // Add project-specific packages
        if (projectData.requirements?.python_packages) {
            const additionalPackages = projectData.requirements.python_packages.join(' ');
            customDockerfile += `\n# Project-specific packages\nRUN conda install -y ${additionalPackages}\n`;
        }
        
        // Add GPU support if needed
        if (projectData.computational_requirements?.gpu_required) {
            customDockerfile = customDockerfile.replace(
                'FROM contextlab/cdl-python:3.7',
                'FROM contextlab/cdl-python:3.7-gpu'
            );
        }
        
        // Add project-specific working directory setup
        customDockerfile += `
# Project-specific setup
WORKDIR /mnt/${projectData.projectId}
COPY . /mnt/${projectData.projectId}/

# Install project dependencies
RUN if [ -f "environment/requirements/base.txt" ]; then pip install -r environment/requirements/base.txt; fi

# Set up Jupyter kernel
RUN python -m ipykernel install --user --name ${projectData.projectId} --display-name "${projectData.title}"
`;
        
        return customDockerfile;
    }
    
    async generateCustomReadme(projectData) {
        return `# ${projectData.title}

${projectData.description}

## Project Information

- **Project ID**: ${projectData.projectId}
- **Status**: ${projectData.status}
- **Created**: ${projectData.created_date}
- **Contributors**: ${projectData.contributors.map(c => c.name).join(', ')}

## Quick Start

1. **Clone the repository**:
   \`\`\`bash
   git clone https://github.com/ContextLab/llmXive.git
   cd llmXive/${projectData.projectId}
   \`\`\`

2. **Set up the environment**:
   \`\`\`bash
   ./setup.sh
   \`\`\`

3. **Launch Jupyter notebook**:
   \`\`\`bash
   docker-compose up jupyter
   \`\`\`

## Project Structure

- \`idea/\`: Initial project concept and brainstorming
- \`technical-design/\`: Technical design documents and specifications
- \`implementation-plan/\`: Implementation planning and milestones
- \`code/\`: Source code, tests, and analysis notebooks
- \`data/\`: Raw and processed datasets
- \`paper/\`: LaTeX manuscript and figures
- \`reviews/\`: Peer reviews and feedback
- \`environment/\`: Computational environment configuration

## Computational Requirements

- **RAM**: ${projectData.computational_requirements?.min_ram_gb || 8}GB minimum
- **Storage**: ${projectData.computational_requirements?.min_storage_gb || 50}GB minimum
- **GPU**: ${projectData.computational_requirements?.gpu_required ? 'Required' : 'Optional'}

## Reproducibility

This project uses Docker and Conda for reproducible computational environments. All dependencies are locked and versioned to ensure consistent results across different systems.

## Citation

If you use this work in your research, please cite:

\`\`\`bibtex
@misc{${projectData.projectId.toLowerCase().replace(/-/g, '_')},
  title={${projectData.title}},
  author={${projectData.contributors.filter(c => c.type === 'human').map(c => c.name).join(' and ')}},
  year={${new Date().getFullYear()}},
  note={llmXive Project ${projectData.projectId}}
}
\`\`\`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
`;
    }
    
    async generateCustomSetupScript(projectData) {
        return `#!/bin/bash

# Project setup script for ${projectData.title}
# Generated by llmXive v2.0

set -e

echo "Setting up ${projectData.title} (${projectData.projectId})..."

# Initialize git submodules (from latex-base template)
if [ -f ".gitmodules" ]; then
    echo "Initializing git submodules..."
    git submodule init
    git submodule update
fi

# Set up conda environment
if [ -f "environment/conda/environment.yml" ]; then
    echo "Creating conda environment..."
    conda env create -f environment/conda/environment.yml -n ${projectData.projectId}
    echo "Activate environment with: conda activate ${projectData.projectId}"
fi

# Build Docker image
if [ -f "Dockerfile" ]; then
    echo "Building Docker image..."
    docker build -t ${projectData.projectId}:latest .
fi

# Set up development environment
if [ -f "environment/docker/docker-compose.yml" ]; then
    echo "Setting up development environment..."
    docker-compose -f environment/docker/docker-compose.yml build
fi

# Create data directories if they don't exist
mkdir -p data/raw data/processed data/synthetic data/external

# Create results directories
mkdir -p paper/figures paper/tables paper/supplements

# Set proper permissions
chmod +x setup.sh

echo "Setup complete! You can now:"
echo "1. Activate conda environment: conda activate ${projectData.projectId}"
echo "2. Launch Jupyter: docker-compose up jupyter"
echo "3. Start coding in the code/ directory"
echo "4. Begin writing in paper/main.tex"

echo ""
echo "For more information, see README.md"
`;
    }
    
    async generateCondaEnvironment(projectData) {
        const pythonVersion = projectData.requirements?.python_version || '3.9';
        const basePackages = [
            'python=' + pythonVersion,
            'numpy',
            'pandas', 
            'matplotlib',
            'seaborn',
            'jupyter',
            'notebook',
            'scikit-learn',
            'scipy'
        ];
        
        // Add project-specific packages
        const projectPackages = projectData.requirements?.python_packages || [];
        const allPackages = [...basePackages, ...projectPackages];
        
        return `name: ${projectData.projectId}
channels:
  - conda-forge
  - defaults
dependencies:
${allPackages.map(pkg => `  - ${pkg}`).join('\n')}
  - pip
  - pip:
    - hypertools
${projectData.requirements?.pip_packages ? projectData.requirements.pip_packages.map(pkg => `    - ${pkg}`).join('\n') : ''}
`;
    }
}
```

### 2. **Enhanced Project Creation Workflow**

```javascript
class EnhancedProjectManager {
    constructor(githubClient, templateManager) {
        this.github = githubClient;
        this.templateManager = templateManager;
        this.repositoryManager = new RepositoryManager(githubClient);
    }
    
    async createProject(projectData) {
        // Step 1: Validate project data
        await this.validateProjectData(projectData);
        
        // Step 2: Generate unique project ID
        const projectId = await this.generateProjectId(projectData.title);
        
        // Step 3: Initialize project from latex-base template
        const initResult = await this.templateManager.initializeProject({
            ...projectData,
            projectId
        });
        
        // Step 4: Set up computational environment
        await this.setupComputationalEnvironment(projectId, projectData);
        
        // Step 5: Create initial project artifacts
        await this.createInitialArtifacts(projectId, projectData);
        
        // Step 6: Set up review system
        await this.initializeReviewSystem(projectId);
        
        // Step 7: Register project in llmXive system
        await this.registerProject(projectId, projectData, initResult);
        
        // Step 8: Set up automated workflows
        await this.setupProjectWorkflows(projectId);
        
        return {
            projectId,
            status: 'created',
            templateVersion: initResult.templateVersion,
            nextSteps: this.getNextSteps(projectId)
        };
    }
    
    async setupComputationalEnvironment(projectId, projectData) {
        const projectPath = `projects/${projectId}`;
        
        // Create Docker Compose configuration
        const dockerCompose = this.generateDockerCompose(projectId, projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/environment/docker/docker-compose.yml`,
            dockerCompose,
            'Add Docker Compose configuration'
        );
        
        // Create development requirements
        const devRequirements = this.generateDevRequirements(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive', 
            `${projectPath}/environment/requirements/dev.txt`,
            devRequirements,
            'Add development requirements'
        );
        
        // Create production requirements  
        const prodRequirements = this.generateProdRequirements(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/environment/requirements/prod.txt`, 
            prodRequirements,
            'Add production requirements'
        );
        
        // Create GitHub Actions workflow for environment testing
        const workflowConfig = this.generateEnvironmentWorkflow(projectId);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/.github/workflows/test-environment.yml`,
            workflowConfig,
            'Add environment testing workflow'
        );
    }
    
    generateDockerCompose(projectId, projectData) {
        return `version: '3.8'

services:
  jupyter:
    build: 
      context: ../..
      dockerfile: Dockerfile
    ports:
      - "8888:8888"
    volumes:
      - ../..:/mnt/${projectId}
      - ../../data:/mnt/${projectId}/data
    environment:
      - JUPYTER_ENABLE_LAB=yes
      - JUPYTER_TOKEN=
    command: >
      bash -c "cd /mnt/${projectId} && 
               jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
    
  analysis:
    build:
      context: ../..
      dockerfile: Dockerfile  
    volumes:
      - ../..:/mnt/${projectId}
      - ../../data:/mnt/${projectId}/data
    working_dir: /mnt/${projectId}
    command: bash
    
  latex:
    image: texlive/texlive:latest
    volumes:
      - ../../paper:/workspace
    working_dir: /workspace
    command: >
      bash -c "while true; do
        inotifywait -e modify,create,delete -r . && 
        pdflatex main.tex && 
        bibtex main && 
        pdflatex main.tex && 
        pdflatex main.tex;
      done"

${projectData.computational_requirements?.gpu_required ? `
  gpu-analysis:
    build:
      context: ../..
      dockerfile: environment/docker/Dockerfile.gpu
    runtime: nvidia
    volumes:
      - ../..:/mnt/${projectId}
      - ../../data:/mnt/${projectId}/data
    working_dir: /mnt/${projectId}
    command: bash
` : ''}
`;
    }
    
    async createInitialArtifacts(projectId, projectData) {
        const projectPath = `projects/${projectId}`;
        
        // Create initial idea document
        const ideaContent = this.generateInitialIdea(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/idea/initial-idea.md`,
            ideaContent,
            'Add initial project idea'
        );
        
        // Create placeholder technical design
        const techDesignContent = this.generateTechnicalDesignPlaceholder(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/technical-design/main.md`,
            techDesignContent,
            'Add technical design placeholder'
        );
        
        // Create basic LaTeX document structure
        const latexContent = this.generateBasicLatexDocument(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/paper/main.tex`,
            latexContent,
            'Add basic LaTeX document structure'
        );
        
        // Create bibliography file
        const bibContent = this.generateBasicBibliography(projectData);
        await this.github.createFile(
            'ContextLab', 'llmXive',
            `${projectPath}/paper/bibliography.bib`,
            bibContent,
            'Add bibliography file'
        );
    }
    
    generateBasicLatexDocument(projectData) {
        return `\\documentclass[12pt]{article}

% Package imports
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{amsmath}
\\usepackage{amsfonts}
\\usepackage{amssymb}
\\usepackage{graphicx}
\\usepackage{natbib}
\\usepackage{url}
\\usepackage{hyperref}
\\usepackage{geometry}
\\usepackage{fancyhdr}
\\usepackage{setspace}

% Page setup
\\geometry{
    letterpaper,
    left=1in,
    right=1in,
    top=1in,
    bottom=1in
}

% Header and footer
\\pagestyle{fancy}
\\fancyhf{}
\\fancyhead[L]{${projectData.title}}
\\fancyhead[R]{${projectData.projectId}}
\\fancyfoot[C]{\\thepage}

% Title information
\\title{${projectData.title}}
\\author{${projectData.contributors.filter(c => c.type === 'human').map(c => c.name).join(' \\and ')}}
\\date{\\today}

% Document settings
\\doublespacing
\\bibliographystyle{plain}

\\begin{document}

\\maketitle

\\begin{abstract}
% Abstract will be generated automatically by llmXive based on project results
This is a placeholder abstract for the ${projectData.title} project. The abstract will be automatically generated based on the project's technical design, implementation, and results.
\\end{abstract}

\\section{Introduction}
% Introduction section - to be developed during paper writing phase
This section will introduce the research problem, motivation, and objectives of the ${projectData.title} project.

\\section{Methods}
% Methods section - to be populated from technical design and implementation
This section will describe the methodology, algorithms, and experimental procedures used in this research.

\\section{Results}
% Results section - to be populated from analysis outputs
This section will present the findings and results of the research.

\\section{Discussion}
% Discussion section - to be developed during paper writing phase
This section will interpret the results and discuss their implications.

\\section{Conclusion}
% Conclusion section - to be developed during paper writing phase
This section will summarize the key findings and suggest future work.

\\section*{Acknowledgments}
We acknowledge the llmXive automated research platform for facilitating this research project.

\\bibliography{bibliography}

\\end{document}
`;
    }
}
```

## Enhanced Database Schema for Template Integration

```sql
-- Add template tracking to projects table
ALTER TABLE projects ADD COLUMN template_source VARCHAR(100) DEFAULT 'ContextLab/latex-base';
ALTER TABLE projects ADD COLUMN template_version VARCHAR(50);
ALTER TABLE projects ADD COLUMN template_initialized_date TIMESTAMP;

-- Project environment table
CREATE TABLE project_environments (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    environment_type ENUM('docker', 'conda', 'pip', 'system') NOT NULL,
    environment_name VARCHAR(255) NOT NULL,
    environment_file_path VARCHAR(500) NOT NULL,
    
    -- Configuration
    python_version VARCHAR(20),
    base_image VARCHAR(255),
    gpu_support BOOLEAN DEFAULT FALSE,
    
    -- Dependencies
    conda_packages JSON,
    pip_packages JSON,
    system_packages JSON,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_built TIMESTAMP,
    build_status ENUM('pending', 'building', 'success', 'failed') DEFAULT 'pending',
    build_log TEXT,
    
    -- Performance
    build_time_seconds INTEGER,
    image_size_mb INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_env (project_id, environment_type),
    INDEX idx_env_status (build_status, is_active),
    UNIQUE KEY unique_project_env (project_id, environment_type, environment_name)
);

-- LaTeX document tracking
CREATE TABLE project_latex_documents (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    document_type ENUM('main', 'supplement', 'appendix', 'poster', 'slides') NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    
    -- Document structure
    sections JSON, -- ["abstract", "introduction", "methods", "results", "discussion"]
    page_count INTEGER,
    word_count INTEGER,
    figure_count INTEGER,
    table_count INTEGER,
    reference_count INTEGER,
    
    -- Build status
    last_compiled TIMESTAMP,
    compile_status ENUM('pending', 'compiling', 'success', 'failed') DEFAULT 'pending',
    compile_log TEXT,
    pdf_path VARCHAR(500),
    
    -- Version tracking
    version VARCHAR(20) DEFAULT '1.0',
    git_commit_hash VARCHAR(40),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_docs (project_id, document_type),
    INDEX idx_compile_status (compile_status),
    INDEX idx_last_compiled (last_compiled)
);

-- Template customizations tracking
CREATE TABLE project_template_customizations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    customization_type ENUM('dockerfile', 'conda_env', 'requirements', 'latex_config', 'github_workflow') NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    
    -- Customization details
    original_content TEXT,
    customized_content TEXT,
    customization_reason TEXT,
    automated BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(255),
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_custom (project_id, customization_type),
    INDEX idx_customization_date (applied_at)
);
```

## Enhanced GitHub Actions for Template Management

### 1. **Project Template Initialization Workflow**

```yaml
name: Initialize Project from Template

on:
  repository_dispatch:
    types: [create-project]

jobs:
  initialize-project:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout llmXive repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.ADMIN_TOKEN }}
          
      - name: Checkout latex-base template
        uses: actions/checkout@v4
        with:
          repository: ContextLab/latex-base
          path: .template
          
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Initialize project from template
        run: |
          node scripts/template/initialize-project.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PROJECT_DATA: ${{ github.event.client_payload.project_data }}
          TEMPLATE_PATH: .template
          
      - name: Set up computational environment
        run: |
          node scripts/template/setup-environment.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PROJECT_ID: ${{ github.event.client_payload.project_data.projectId }}
          
      - name: Create initial artifacts
        run: |
          node scripts/template/create-artifacts.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PROJECT_ID: ${{ github.event.client_payload.project_data.projectId }}
          PROJECT_DATA: ${{ github.event.client_payload.project_data }}
          
      - name: Commit project initialization
        run: |
          git config --local user.email "llmxive@contextlab.ai"
          git config --local user.name "llmXive Project Manager"
          git add .
          git commit -m "🚀 Initialize project ${{ github.event.client_payload.project_data.projectId }} from latex-base template"
          git push
          
      - name: Update project registry
        run: |
          node scripts/template/update-registry.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PROJECT_ID: ${{ github.event.client_payload.project_data.projectId }}
```

### 2. **Environment Testing Workflow**

```yaml
name: Test Project Environment

on:
  push:
    paths:
      - 'projects/*/Dockerfile'
      - 'projects/*/environment/**'
      - 'projects/*/setup.sh'
  pull_request:
    paths:
      - 'projects/*/Dockerfile'
      - 'projects/*/environment/**'
      - 'projects/*/setup.sh'

jobs:
  test-environments:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: ${{ fromJson(github.event.client_payload.projects || '[]') }}
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Test Docker build
        run: |
          cd projects/${{ matrix.project }}
          docker build -t ${{ matrix.project }}:test .
          
      - name: Test Conda environment
        run: |
          cd projects/${{ matrix.project }}
          if [ -f "environment/conda/environment.yml" ]; then
            docker run --rm -v $(pwd):/workspace ${{ matrix.project }}:test \
              bash -c "conda env create -f /workspace/environment/conda/environment.yml --name test-env"
          fi
          
      - name: Test setup script
        run: |
          cd projects/${{ matrix.project }}
          if [ -f "setup.sh" ]; then
            docker run --rm -v $(pwd):/workspace ${{ matrix.project }}:test \
              bash -c "cd /workspace && chmod +x setup.sh && ./setup.sh"
          fi
          
      - name: Test LaTeX compilation
        run: |
          cd projects/${{ matrix.project }}
          if [ -f "paper/main.tex" ]; then
            docker run --rm -v $(pwd)/paper:/workspace texlive/texlive:latest \
              bash -c "cd /workspace && pdflatex main.tex"
          fi
```

## Integration Benefits

### 1. **Standardization**
- All projects follow the established ContextLab latex-base template
- Consistent computational environments across projects
- Standardized LaTeX document structure
- Uniform project organization

### 2. **Reproducibility** 
- Docker-based computational environments
- Locked dependency versions
- Version-controlled environment configurations
- Consistent build processes

### 3. **Automation**
- Automated project initialization from template
- Automated environment testing
- Automated LaTeX compilation
- Automated dependency management

### 4. **Professional Quality**
- Publication-ready LaTeX documents
- Professional project structure
- Comprehensive documentation
- Industry-standard practices

This enhanced design seamlessly integrates the ContextLab latex-base template while maintaining all llmXive v2.0 functionality, ensuring that every research project follows professional standards for reproducibility and presentation.