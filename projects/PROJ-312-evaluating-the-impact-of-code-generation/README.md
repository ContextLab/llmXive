# Evaluating the Impact of Code Generation on Code Review Turnaround Time

**Project ID**: PROJ-312

## Overview
This project investigates whether AI-assisted code generation (e.g., GitHub Copilot) significantly impacts the turnaround time of code reviews compared to human-written code.

## Methodology
1. **Data Acquisition**: Fetch PR metadata from top Python and JavaScript repositories via GitHub API.
2. **Classification**: Label PRs as "AI-assisted" or "Non-AI" based on commit messages and labels.
3. **Analysis**: Perform statistical testing (Mann-Whitney U) on turnaround times.
4. **Visualization**: Generate boxplots comparing distributions.

## Directory Structure
- `code/`: Source code for data fetching, analysis, and reporting.
- `data/`: Raw and processed datasets.
- `tests/`: Unit and contract tests.
- `artifacts/`: Final reports and visualizations.
- `contracts/`: JSON schema definitions for data validation.

## Prerequisites
- Python 3.11+
- GitHub Personal Access Token (set as `GITHUB_TOKEN` environment variable)

## Quick Start
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Run the data acquisition pipeline:
 ```bash
 python code/fetch_data.py
 ```
3. Run the analysis pipeline:
 ```bash
 python code/analyze.py
 ```

## License
MIT
