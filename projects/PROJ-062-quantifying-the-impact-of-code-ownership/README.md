# PROJ-062: Quantifying the Impact of Code Ownership on Software Quality

## Overview
This project analyzes the relationship between code ownership (measured via Gini coefficient) and software quality (bug density) across multiple open-source repositories.

## Project Structure
- `code/`: Source code for data collection, metrics calculation, and statistical analysis
- `data/`: Raw, intermediate, and results data directories
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents
- `figures/`: Generated visualizations
- `state/`: State management snapshots

## Prerequisites
- Python 3.11+
- Git
- GitHub API token (for rate limit access)

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables (see `code/config.py`)
3. Run the pipeline: `python code/main.py`

## Key Outputs
- `data/results/final_report.json`: Statistical analysis results
- `data/results/linkage_rate.json`: Bug-file linkage metrics
- `figures/*.png`: Scatter plots and visualizations
