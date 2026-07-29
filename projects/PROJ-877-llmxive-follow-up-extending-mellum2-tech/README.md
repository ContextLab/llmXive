# llmXive: Extending Mellum2 Technical Report

**Project ID**: PROJ-877-llmxive-follow-up-extending-mellum2-tech

## Overview

This project implements an automated research pipeline to investigate the relationship between static code complexity metrics and the prediction loss of Large Language Models (LLMs). It extends the findings of the "Mellum2 Technical Report" by introducing rigorous statistical validation, non-linear threshold detection, and cross-language consistency checks.

The pipeline is designed to be fully reproducible, running on real data from the `codeparrot/github-code` dataset, and adhering to strict compute constraints (CPU-only, streaming).

## Key Objectives

1. **Correlation Analysis**: Compute Pearson and Spearman correlations between static complexity metrics (cyclomatic complexity, nesting depth) and LLM prediction loss (normalized by n-gram baseline).
2. **Threshold Detection**: Identify structural thresholds where the complexity-loss relationship shifts using piecewise regression and change-point detection.
3. **Statistical Validation**: Perform permutation tests, power analysis, and multiple-comparison corrections to ensure statistical significance.
4. **Cross-Language Consistency**: Validate findings across Python and Java codebases to ensure generalizability.

## Project Structure

```text
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis modules
│ ├── contracts/ # Data schemas
│ ├── data/ # Data loading and preprocessing
│ ├── inference/ # LLM inference engine
│ ├── utils/ # Logging, timeouts, helpers
│ ├── config.py # Global configuration
│ └── main.py # Pipeline orchestration
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data (immutable)
│ ├── processed/ # Annotated and processed data
│ └── results/ # Analysis outputs (JSON, PNG)
├── tests/ # Unit and integration tests
├── specs/ # Design documents and requirements
├── requirements.txt # Python dependencies
├──.gitignore # Git ignore rules
└── README.md # This file
```

## Prerequisites

- Python 3.9+
- Hugging Face Hub account (for dataset access)
- Sufficient disk space (for dataset streaming and caching)
- CPU-only environment (as per project constraints)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Configure environment variables (e.g., Hugging Face token):
 ```bash
 cp.env.example.env
 # Edit.env and add your HF_TOKEN
 ```

## Usage

### Running the Pipeline

The entire pipeline is orchestrated via `code/main.py`. Ensure all prerequisites (Feasibility Check) are met before running.

```bash
python code/main.py
```

### Running Specific Tasks

Individual modules can be run directly for debugging or specific analysis steps:

```bash
# Feasibility Check
python code/analysis/feasibility.py

# Download Data
python code/data/download.py

# Correlation Analysis
python code/analysis/correlation.py
```

### Running Tests

```bash
pytest tests/ -v
```

## Workflow

1. **Phase 0: Setup & Feasibility**: Initialize directories, fetch pilot metadata, and determine feasible sample size.
2. **Phase 1: Correlation Analysis**: Download data, preprocess with static analysis, run LLM inference, and compute correlations.
3. **Phase 2: Threshold Detection**: Apply piecewise regression to identify non-linear shifts in the data.
4. **Phase 3: Statistical Validation**: Perform permutation tests and power analysis to validate results.

## Results

All generated artifacts (JSON reports, plots, logs) are stored in `data/results/`. Key outputs include:

- `feasibility_report.json`: Sample size determination.
- `us1_correlation_stats.json`: Correlation coefficients and p-values.
- `us1_correlation_plot.png`: Scatter plots of complexity vs. loss.
- `us2_threshold_report.md`: Threshold detection analysis.
- `us3_power_analysis.json`: Statistical power validation.

## Contributing

This project follows a strict "Real Data Only" policy. Do not use synthetic data or placeholders. All implementations must run against the real `codeparrot/github-code` dataset.

## License

[Insert License Here]