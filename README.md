# llmXive - Automated Scientific Discovery Platform

> **Active refactor (branch `001-agentic-pipeline-refactor`)** — the platform is
> being rewritten as a Spec-Kit-per-project agentic pipeline running on free
> LLM backends (Dartmouth Chat + Hugging Face). Authoritative docs while
> the refactor is in flight:
>
> - Constitution: [.specify/memory/constitution.md](.specify/memory/constitution.md)
> - Spec: [specs/001-agentic-pipeline-refactor/spec.md](specs/001-agentic-pipeline-refactor/spec.md)
> - Plan: [specs/001-agentic-pipeline-refactor/plan.md](specs/001-agentic-pipeline-refactor/plan.md)
> - Quickstart: [specs/001-agentic-pipeline-refactor/quickstart.md](specs/001-agentic-pipeline-refactor/quickstart.md)
> - Agent registry: [agents/registry.yaml](agents/registry.yaml) (28 agents on Qwen 3.5 122B / Gemma 3 27B via Dartmouth Chat)
> - Prompt library: [agents/prompts/](agents/prompts/) (one file per agent, referenced by `prompt_path:` in the registry)
> - Pipeline thresholds: [web/about.html](web/about.html) (machine-readable `data-threshold` spans)
>
> The legacy `code/llmxive-automation/` tree is being deleted in this refactor;
> see `scripts/migrate_legacy_layout.py`. The new agentic implementation lives
> under [src/llmxive/](src/llmxive/) and [agents/](agents/).
>
> **New-contributor onramp (SC-008)**: open
> [agents/registry.yaml](agents/registry.yaml) → pick the lifecycle stage you
> want to understand → follow the agent's `prompt_path:` to its definition.
> This should take about 5 minutes from a cold start.

---

llmXive is a comprehensive automated system for scientific discovery that leverages large language models (LLMs) to orchestrate the complete research pipeline from idea generation through publication. The platform manages research projects through five distinct stages with integrated review processes and quality assurance.

## 🎯 Project Overview

llmXive transforms the traditional research process by automating and systematizing scientific discovery:

- **Automated Research Pipeline**: Complete workflow from idea generation to published papers
- **Multi-LLM Integration**: Leverages OpenAI GPT, Google Gemini, and Anthropic Claude models
- **Quality Assurance**: Integrated review system with iterative improvement cycles
- **Project Management**: Structured organization with GitHub integration and web interface
- **Reproducible Research**: Standardized project structure with version control and documentation

## 🏗️ Architecture

### Core Components

- **Pipeline Orchestrator** (`scripts/llmxive-cli.py`): Main automation engine
- **Project Management System** (`projects/`): Unified project organization
- **Web Interface** (`web/`): Dashboard for project tracking and visualization
- **Review System** (`prompts/`): Modular prompt templates for quality control
- **Database Layer** (`web/database/`): Project metadata and analytics

### Pipeline Stages

1. **Idea Generation**: Brainstorm novel research concepts in specified fields
2. **Technical Design**: Create detailed technical specifications and methodologies
3. **Implementation Planning**: Develop structured implementation roadmaps
4. **Code Development**: Generate executable code and data collection procedures
5. **Data Analysis**: Perform statistical analysis and interpret results
6. **Paper Writing**: Produce complete research papers in LaTeX format
7. **Review & Refinement**: Iterative improvement through automated review cycles

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **LaTeX distribution** (TeX Live or MacTeX)
- **Git**
- **API Keys** for at least one LLM provider:
  - OpenAI API Key
  - Google Gemini API Key
  - Anthropic Claude API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/llmXive.git
   cd llmXive
   ```

2. **Install dependencies**
   ```bash
   npm install
   pip install -r requirements.txt  # If requirements.txt exists
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file or export directly
   export OPENAI_API_KEY="your_openai_key_here"
   export GOOGLE_API_KEY="your_google_key_here"
   export ANTHROPIC_API_KEY="your_anthropic_key_here"
   ```

4. **Verify LaTeX installation**
   ```bash
   which pdflatex
   # Should return path to pdflatex
   ```

### Basic Usage

#### Run Complete Pipeline
```bash
# Generate a complete research project
python scripts/llmxive-cli.py --field biology

# Specify custom parameters
python scripts/llmxive-cli.py --field "materials science" --iterations 5
```

#### Web Interface
```bash
# Start the web server (if applicable)
cd web
python -m http.server 8000
# Visit http://localhost:8000
```

#### Project Management
```bash
# Update project database
node scripts/update-database.js

# Generate project reports
node scripts/generate-review-summary.js
```

## 📁 Project Structure

```
llmXive/
├── projects/                     # Unified project directory
│   ├── PROJ-001-gene-regulation/
│   │   ├── .llmxive/
│   │   │   └── config.json      # Project configuration
│   │   ├── idea/                # Initial research idea
│   │   ├── technical-design/    # Technical specifications
│   │   ├── implementation-plan/ # Implementation roadmap
│   │   ├── code/               # Generated code and scripts
│   │   ├── data/               # Data collection and analysis
│   │   ├── paper/              # Research paper and LaTeX files
│   │   └── reviews/            # Review feedback and iterations
│   └── PROJ-XXX-*/             # Additional projects...
├── prompts/                     # Modular prompt templates
│   ├── README.md               # Prompt system documentation
│   ├── idea_generation.md      # Idea generation prompts
│   ├── technical_design.md     # Technical design prompts
│   ├── implementation_plan.md  # Planning prompts
│   ├── code_generation.md      # Code generation prompts
│   ├── data_analysis.md        # Analysis prompts
│   ├── paper_writing.md        # Paper writing prompts
│   ├── latex_fixing.md         # LaTeX repair prompts
│   └── review_*.md             # Review and revision prompts
├── scripts/                     # Automation and utility scripts
│   ├── llmxive-cli.py          # Main pipeline orchestrator
│   ├── update-database.js      # Database synchronization
│   ├── generate-review-summary.js # Review aggregation
│   └── migrate-projects.js     # Project migration utilities
├── web/                        # Web interface and dashboard
│   ├── index.html             # Main dashboard
│   ├── projects.html          # Project management interface
│   ├── database/              # Project metadata and analytics
│   │   ├── projects.json      # Project database
│   │   ├── contributors.json  # Contributor information
│   │   └── analytics.json     # Usage analytics
│   ├── css/                   # Styling and themes
│   ├── js/                    # Frontend JavaScript
│   └── docs/                  # Documentation and guides
├── notes/                      # Development notes and planning
├── tests/                      # Test suites
├── .github/                    # GitHub Actions and workflows
└── README.md                  # This file
```

## 🔧 Configuration

### Project Configuration
Each project contains a `.llmxive/config.json` file with metadata:
```json
{
  "id": "PROJ-001-gene-regulation",
  "title": "Gene Regulation Mechanisms",
  "field": "biology",
  "status": "in-progress",
  "created": "2025-07-09T12:00:00Z",
  "phases": {
    "idea": {"status": "completed"},
    "technical_design": {"status": "completed"},
    "implementation_plan": {"status": "in-progress"},
    "code": {"status": "pending"},
    "paper": {"status": "pending"}
  }
}
```

### Prompt System
The modular prompt system allows easy customization:
- Edit templates in `prompts/` directory
- Use `{variable}` syntax for dynamic content
- Templates automatically loaded by the pipeline
- Fallback prompts available if files are missing

## 💻 Development

### Adding New Features

1. **New Pipeline Stage**: Add prompt template and update orchestrator
2. **New Review Type**: Create prompt in `prompts/review_*.md`
3. **New Project Type**: Extend project structure and database schema
4. **New LLM Provider**: Add client in `APIModelClient` class

### Testing

```bash
# Run test suite
npm test

# Test specific components
python -m pytest tests/

# Test prompt loading
python -c "from scripts.llmxive_cli import PromptLoader; print('Prompts OK')"
```

### Code Quality

```bash
# Format code
npm run format

# Lint JavaScript
npm run lint

# Validate project structure
node scripts/validate-structure.js
```

## 📊 Monitoring and Analytics

### Project Tracking
- **Web Dashboard**: Real-time project status and progress
- **Database Analytics**: Usage patterns and performance metrics
- **Review Metrics**: Quality scores and improvement trends
- **Pipeline Logs**: Detailed execution and error tracking

### Quality Assurance
- **Automated Reviews**: Multi-LLM review system with scoring
- **Iterative Improvement**: Automatic revision cycles
- **LaTeX Validation**: Document structure and compilation checks
- **Reference Validation**: Citation and bibliography verification

## 🤝 Contributing

### Getting Started
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines
- Follow existing code style and patterns
- Add comprehensive documentation
- Include test coverage for new features
- Update README and documentation as needed
- Ensure backwards compatibility

### Project Structure Conventions
- Use `PROJ-###-descriptive-name` format for project IDs
- Follow standardized directory structure for all projects
- Include proper metadata in `.llmxive/config.json`
- Document all prompt templates with variables and usage

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [Full documentation](web/docs/)
- **Issue Tracker**: [GitHub Issues](https://github.com/yourusername/llmXive/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/llmXive/discussions)

## 🙏 Acknowledgments

- OpenAI, Google, and Anthropic for providing LLM APIs
- The scientific research community for inspiration and validation
- Contributors and maintainers of the project

---

*llmXive is a research project exploring the intersection of artificial intelligence and scientific discovery. Use responsibly and always validate results through appropriate peer review processes.*