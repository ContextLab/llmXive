# Quick Start Guide

This guide provides instructions for installing dependencies and running the automated science pipeline for investigating the correlation between code churn and technical debt.

## Prerequisites

- Python 3.11 or higher
- Git
- pip (Python package installer)
- System packages required for Semgrep:
 - On Ubuntu/Debian: `sudo apt-get install -y python3-pip`
 - On macOS: Ensure Homebrew is installed and run `brew install python`

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` file includes the following key dependencies:
 - `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`: For data processing and statistical analysis
 - `matplotlib`, `seaborn`: For visualization
 - `pydriller`: For git history analysis
 - `radon`: For Python code complexity metrics
 - `semgrep`: For multi-language static analysis
 - `tqdm`: For progress bars
 - `requests`: For API interactions

4. **Verify tool availability**:
 The pipeline will automatically check for `radon` and `semgrep` upon execution. Ensure they are installed:
 ```bash
 radon --version
 semgrep --version
 ```

## Execution

The pipeline is orchestrated via `code/main.py`. Run the full pipeline or individual steps as needed.

### Run the Full Pipeline

To execute the entire pipeline (Data Extraction → Static Analysis → Preprocessing → Analysis → Visualization → Reporting):

```bash
python code/main.py --full-pipeline
```

### Run Individual Steps

You can execute specific stages of the pipeline independently:

- **Data Extraction**:
 ```bash
 python code/main.py --step data_extraction
 ```
 Outputs: `data/raw/repos_metadata.csv`, `data/raw/git_metrics.csv`

- **Static Analysis**:
 ```bash
 python code/main.py --step static_analysis
 ```
 Outputs: `data/raw/static_analysis_metrics.csv`

- **Preprocessing**:
 ```bash
 python code/main.py --step preprocessing
 ```
 Outputs: `data/processed/unified_metrics.csv`, parameterized datasets for sensitivity analysis

- **Analysis**:
 ```bash
 python code/main.py --step analysis
 ```
 Outputs: `data/results/correlation_results.csv`, `data/results/sensitivity_analysis.csv`, `data/results/meta_analysis_results.csv`

- **Visualization**:
 ```bash
 python code/main.py --step visualization
 ```
 Outputs: `data/results/plots/*.png`

- **Reporting**:
 ```bash
 python code/main.py --step reporting
 ```
 Outputs: `data/results/summary_report.txt`

### Configuration

Default parameters (e.g., LOC thresholds, repository limits) are defined in `code/config.py`. You can override environment variables or modify the config file directly for custom runs.

## Output Files

All output files are generated under the `data/` directory:

- **Raw Data**: `data/raw/`
 - `repos_metadata.csv`: Repository metadata (stars, age, language)
 - `git_metrics.csv`: Git history metrics per file
 - `static_analysis_metrics.csv`: Static analysis results (CC, code smells, debt score)
 - `tool_validation_log.csv`: Tool availability and validation status

- **Processed Data**: `data/processed/`
 - `unified_metrics.csv`: Unified dataset with raw metrics (`total_lines_changed`, `debt_score`, `avg_loc`, `contributor_count`)
 - Parameterized datasets for sensitivity analysis (thresholds: 5, 10, 20)

- **Results**: `data/results/`
 - `correlation_results.csv`: Correlation coefficients and p-values
 - `sensitivity_analysis.csv`: Results across different LOC thresholds
 - `meta_analysis_results.csv`: Meta-analysis of Fisher-transformed r coefficients
 - `plots/`: Scatter plots with regression lines
 - `summary_report.txt`: Comprehensive summary of findings

## Validation

- **Contract Tests**: Run tests in `tests/contract/` to verify schema compliance.
- **Integration Tests**: Run tests in `tests/integration/` to validate end-to-end functionality.

```bash
pytest tests/
```

## Troubleshooting

- **Missing Tools**: If `radon` or `semgrep` are not found, install them via `pip` or `brew`.
- **API Rate Limits**: The pipeline uses the GitHub API. If you encounter rate limits, configure a personal access token via the `GITHUB_TOKEN` environment variable.
- **Timeouts**: Long-running steps (e.g., cloning large repos) may timeout. Adjust the timeout threshold in `code/main.py` if necessary.

## Next Steps

- Review the `research.md` file for detailed methodology.
- Explore the `specs/` directory for design documents and user stories.
- Contribute by implementing additional tasks from `tasks.md`.