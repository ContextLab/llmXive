# llmXive Automation System - Project llmxive-auto-001

This project implements the fully autonomous scientific discovery pipeline for llmXive.

## Project Overview

The llmXive Automation System enables fully automated scientific research by:
- Dynamically selecting appropriate language models from HuggingFace
- Analyzing project board state to determine next actions
- Executing research tasks (brainstorming, design, implementation, paper writing)
- Managing the complete project lifecycle through GitHub integration

## Installation

From the parent directory:

```bash
cd ../helpers
pip install -e .
```

## Running the Automation

### Local Execution

```bash
# Full automation cycle
python -m llmxive_automation

# Specific task
python -m llmxive_automation --mode single-task --task brainstorm_ideas

# Dry run
python -m llmxive_automation --dry-run
```

### GitHub Actions

The system runs automatically every 3 hours via GitHub Actions. To manually trigger:

1. Navigate to the Actions tab in the repository
2. Select "llmXive Automation" workflow
3. Click "Run workflow"

## Environment Setup

Required environment variables:
- `GITHUB_TOKEN`: GitHub API token with repo and project permissions
- `HF_TOKEN`: (Optional) HuggingFace API token for accessing private models

## Testing

```bash
# Run all tests
pytest ../tests/

# Run with coverage
pytest --cov=llmxive_automation ../tests/
```

## Special Considerations

- **Resource Constraints**: Designed to run within GitHub Actions free tier limits
- **Model Size**: Limited to models ≤7GB to fit in constrained environments
- **Rate Limits**: Implements exponential backoff for API calls
- **Checkpointing**: Tasks are designed to be resumable in case of interruption

## Architecture

The system consists of:
1. **Model Selector**: Chooses appropriate LLMs from HuggingFace
2. **Task Orchestrator**: Determines next actions based on project state
3. **GitHub Manager**: Handles all repository and project board operations
4. **Prompt Builder**: Constructs efficient prompts for different task types

## Related Resources

- [Technical Design Document](../../technical_design_documents/llmXive_automation/design.md)
- [GitHub Issue #21](https://github.com/ContextLab/llmXive/issues/21)