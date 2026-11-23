# llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Project Documentation

This directory contains documentation for the llmXive Drift Detection pipeline.

### Contents

- **README.md**: This file, providing an overview of the project structure and documentation organization.
- **quickstart.md**: (To be created in T043a) Step-by-step guide for running the drift detection pipeline.
- **data-model.md**: (To be created in T043b) Specification of data schemas and field definitions.
- **api.md**: (Future) API reference for the core modules.

## Overview

This project implements a zero-shot drift detection system to identify novel attack patterns in LLM interaction logs by comparing them against a known taxonomy of safety categories.

### Key Features

- **Zero-Shot Drift Scoring**: Computes cosine distances between log embeddings and taxonomy centroids.
- **Human-in-the-Loop Validation**: Stratifies logs for human annotation to validate drift scores.
- **Baseline Comparison**: Compares drift detection performance against a local zero-shot LLM classifier.

## Directory Structure

```
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/
├── code/ # Source code modules
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Processed data and results
│ └── test/ # Test fixtures and static logs
├── docs/ # This directory: project documentation
├── specs/ # Design documents and requirements
└── tests/ # Unit and integration tests
```

## Getting Started

1. Ensure all prerequisites are installed (see `requirements.txt`).
2. Configure the project using `code/config.py`.
3. Run the full pipeline with `python code/run_full_pipeline.py`.

For detailed instructions, see `quickstart.md` (coming soon).

## License

[Project License Placeholder]
