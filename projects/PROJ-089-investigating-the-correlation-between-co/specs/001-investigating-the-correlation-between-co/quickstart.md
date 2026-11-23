# Quickstart: Investigating the Correlation Between Code Churn and Technical Debt

## Prerequisites

- **Python**: 3.11+
- **Git**: Installed and in PATH.
- **Semgrep**: `pip install semgrep==1.30.0` (or use the pinned `requirements.txt`).
- **Access**: Public GitHub repositories (no token required for public repos).

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd proj-089-code-churn-debt
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

### 1. Full Pipeline Execution
Run the complete extraction, analysis, and reporting pipeline:
```bash
python code/main.py --full
```
*Note: This may take up to 6 hours depending on the number of repositories.*

### 2. Mock Run (Fast Test)
Run a quick test with a single mock repository to verify logic:
```bash
python code/main.py --mock
```
*This generates dummy data and runs the statistical models without cloning real repos.*

### 3. Specific Phases
- **Extraction Only**:
 ```bash
 python code/extraction.py --repos data/raw/repos_metadata.csv
 ```
- **Analysis Only** (requires `data/processed/unified_metrics.csv`):
 ```bash
 python code/analysis.py
 ```
- **Reporting Only** (requires `data/processed/correlation_results.csv`):
 ```bash
 python code/reporting.py
 ```

## Output Artifacts

After a successful run, the following files will be generated in `data/processed/`:
- `unified_metrics.csv`: Raw metrics for all files.
- `unified_metrics_loc5.csv`: Filtered by avg_loc >= 5.
- `unified_metrics_loc10.csv`: Filtered by avg_loc >= 10.
- `unified_metrics_loc20.csv`: Filtered by avg_loc >= 20.
- `correlation_results.csv`: Per-repo regression slopes.
- `meta_analysis_results.csv`: Aggregated meta-analysis results.
- `summary_report.txt`: Final human-readable report.

## Troubleshooting

- **Semgrep Error**: Ensure `semgrep==1.30.0` is installed. Some languages may not be supported.
- **Timeout**: If the pipeline exceeds 6 hours, reduce the number of repositories in `data/raw/repos_metadata.csv`.
- **Memory Error**: The pipeline streams data; if memory is exhausted, check for infinite loops in `git log` parsing.
