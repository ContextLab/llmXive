# llmXive Automation System

This codebase implements the fully autonomous scientific discovery pipeline for llmXive. It automatically generates research ideas, develops them into papers, and manages the entire project lifecycle using language models.

## Overview

The system runs as a GitHub Action every 3 hours, dynamically selecting appropriate models from HuggingFace and executing research tasks based on the current project state.

## Installation

```bash
# Install the package
pip install -e helpers/

# Or install with development dependencies
pip install -e "helpers/[dev]"
```

## Usage

### Command Line Interface

```bash
# Run a full automation cycle
python -m llmxive_automation.main

# Run a specific task
python -m llmxive_automation.main --task brainstorm_ideas

# Dry run mode (preview without executing)
python -m llmxive_automation.main --dry-run

# Use a specific model
python -m llmxive_automation.main --model "microsoft/phi-2"
```

### GitHub Actions

The system runs automatically via GitHub Actions. To trigger manually:

1. Go to Actions tab in the repository
2. Select "llmXive Automation" workflow
3. Click "Run workflow"

## Architecture

- **Model Selection**: Dynamically chooses trending small models from HuggingFace
- **Task Orchestration**: Manages the research pipeline based on project state
- **GitHub Integration**: Handles issues, commits, and project board updates
- **Quality Assurance**: Validates references and ensures scientific rigor

## Development

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=llmxive_automation tests/

# Format code
black helpers/ tests/

# Lint code
flake8 helpers/ tests/
```

## Configuration

Environment variables:
- `GITHUB_TOKEN`: GitHub API token (required)
- `HF_TOKEN`: HuggingFace API token (optional, for private models)
- `LLMXIVE_MODEL`: Override default model selection
- `LLMXIVE_DRY_RUN`: Run in preview mode without making changes