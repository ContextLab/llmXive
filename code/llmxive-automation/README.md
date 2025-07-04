# llmXive Automation System

Automated scientific discovery system that uses small language models to drive the llmXive research pipeline.

## Overview

This system automates the entire llmXive workflow from idea generation to paper publication using small (<3.5GB) instruct-tuned models from HuggingFace. It runs as a GitHub Action every 3 hours or can be executed locally.

## Features

- **Dynamic Model Selection**: Automatically selects trending small models from HuggingFace
- **4-bit Quantization**: Runs large models in memory-constrained environments
- **Complete Task Coverage**: Supports 40+ task types covering the entire research pipeline
- **Self-Correcting**: Can identify and implement improvements to its own outputs
- **GitHub Integration**: Full integration with issues, labels, and project boards

## Installation

```bash
# Clone the repository
git clone https://github.com/ContextLab/llmXive.git
cd llmXive/code/llmxive-automation

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Local Execution

```bash
# Set environment variables
export GITHUB_TOKEN=your_github_token
export HF_TOKEN=your_huggingface_token  # Optional

# Run full automation cycle
python main.py --max-tasks 5

# Run specific task
python main.py --task BRAINSTORM_IDEA

# Use CLI for more control
python cli.py --help
```

### GitHub Actions

The automation runs automatically every 3 hours. You can also trigger it manually:

1. Go to Actions tab in GitHub
2. Select "llmXive Automation" workflow
3. Click "Run workflow"
4. Optionally specify max tasks or specific task type

## Task Types

### Ideation & Design
- `BRAINSTORM_IDEA` - Generate new research ideas
- `WRITE_TECHNICAL_DESIGN` - Create technical design documents
- `REVIEW_TECHNICAL_DESIGN` - Review and score designs

### Planning
- `WRITE_IMPLEMENTATION_PLAN` - Convert designs to implementation plans
- `REVIEW_IMPLEMENTATION_PLAN` - Review implementation plans

### Literature & Research
- `CONDUCT_LITERATURE_SEARCH` - Search llmXive archive
- `VALIDATE_REFERENCES` - Check reference validity
- `MINE_LLMXIVE_ARCHIVE` - Find related internal work

### Code Development
- `WRITE_CODE` - Implement modules following plans
- `WRITE_TESTS` - Create comprehensive test suites
- `RUN_TESTS` - Execute tests
- `DEBUG_CODE` - Fix failing code
- `ORGANIZE_INTO_NOTEBOOKS` - Create Jupyter notebooks

### Data & Analysis
- `GENERATE_DATASET` - Design datasets
- `ANALYZE_DATA` - Perform statistical analysis
- `PLAN_STATISTICAL_ANALYSIS` - Design analysis approach
- `INTERPRET_RESULTS` - Interpret findings

### Visualization
- `PLAN_FIGURES` - Design paper figures
- `CREATE_FIGURES` - Generate publication-quality figures
- `VERIFY_FIGURES` - Check figure quality

### Paper Writing
- `WRITE_ABSTRACT`, `WRITE_INTRODUCTION`, `WRITE_METHODS`
- `WRITE_RESULTS`, `WRITE_DISCUSSION`
- `COMPILE_BIBLIOGRAPHY`

### Review & Quality
- `REVIEW_PAPER` - Comprehensive paper review
- `REVIEW_CODE` - Code quality review
- `CHECK_REPRODUCIBILITY` - Verify reproducibility
- `CHECK_LOGIC_GAPS` - Find logical inconsistencies

### Project Management
- `CHECK_PROJECT_STATUS` - Check advancement criteria
- `UPDATE_PROJECT_STAGE` - Move between pipeline stages
- `CREATE_ISSUE_COMMENT` - Add issue comments
- `FORK_IDEA` - Create related ideas

## Testing

```bash
# Run unit tests
python run_tests.py --unit

# Run integration tests (requires GPU)
python run_tests.py --integration

# Run specific test
python run_tests.py --test tests/unit/test_response_parser.py

# Run quick smoke tests
python run_tests.py --quick
```

## Architecture

```
src/
├── model_manager.py      # HuggingFace model selection and loading
├── conversation_manager.py # Model-specific prompt formatting
├── github_handler.py     # GitHub API operations
├── response_parser.py    # Parse various LLM output formats
├── task_executor.py      # Execute all task types
└── orchestrator.py       # Main automation logic

tests/
├── unit/                 # Unit tests with mocked dependencies
└── integration/          # Integration tests with real models
```

## Configuration

### Environment Variables
- `GITHUB_TOKEN` - Required for GitHub API access
- `HF_TOKEN` - Optional, for private HuggingFace models
- `CUDA_VISIBLE_DEVICES` - Control GPU usage

### Model Selection Criteria
- Size < 3.5GB (for GitHub Actions runners)
- Has "instruct" or "chat" tags
- Trending on HuggingFace
- Supports text generation

## Contributing

1. Add new task types in `task_executor.py`
2. Update task type lists in documentation
3. Add unit tests for new functionality
4. Test with real models locally before pushing

## Troubleshooting

### Out of Memory Errors
- The system uses 4-bit quantization by default
- Try setting `CUDA_VISIBLE_DEVICES=""` to use CPU
- Reduce `max_new_tokens` in task configurations

### Model Loading Failures
- Check internet connection
- Verify HuggingFace is accessible
- Try clearing cache: `rm -rf ~/.cache/huggingface`

### GitHub API Rate Limits
- Ensure GITHUB_TOKEN has appropriate permissions
- The system implements rate limiting automatically

## License

Same as llmXive project - see main repository LICENSE file.