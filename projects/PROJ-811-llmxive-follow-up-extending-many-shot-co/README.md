# PROJ-811-llmxive-follow-up-extending-many-shot-co

## Project Structure

This project implements the llmXive automated science pipeline for analyzing logical dependency vs. semantic curvature in many-shot in-context learning.

### Directory Layout

- `code/src/`: Core Python modules (parser, inference, analysis, etc.)
- `code/scripts/`: Executable scripts for data processing and pipeline steps
- `code/tests/`: Unit and integration tests
- `data/raw/`: Raw downloaded datasets
- `data/processed/`: Intermediate processed data (DAGs, manifests)
- `data/results/`: Final inference results and statistical outputs
- `artifacts/`: Checksums, state files, and reports
- `specs/`: Design documents and feature specifications
- `docs/`: Documentation
- `config/`: Configuration files
- `figures/`: Generated plots and images

### Quick Start

1. Run the setup script to ensure directories exist:
 ```bash
 python code/scripts/setup_project_structure.py
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run tests:
 ```bash
 pytest code/tests/
 ```