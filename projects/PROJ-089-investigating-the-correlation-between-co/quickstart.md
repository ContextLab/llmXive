# Quickstart Guide: Code Churn vs Technical Debt Correlation Study

## Prerequisites

- Python 3.11+
- Git
- Semgrep CLI (v1.30.0) installed and in PATH

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
4. Install Semgrep (if not already installed):
 ```bash
 pip install semgrep==1.30.0
 ```

## Execution

Run the full pipeline from the project root:

```bash
python code/main.py
```

### Expected Output

Upon successful completion, the following artifacts will be generated:

- **Data**:
 - `data/processed/unified_metrics.csv`: Unified metrics for all analyzed files.
 - `data/results/correlation_results.csv`: Pearson and Spearman correlation coefficients.
 - `data/results/meta_analysis_results.csv`: Combined meta-analysis results.
 - `data/results/sensitivity_analysis.csv`: Sensitivity analysis at LOC thresholds 5, 10, 20.
- **Visualizations**:
 - `data/results/plots/`: Scatter plots with regression lines for each repository.
- **Reports**:
 - `data/results/summary_report.txt`: Comprehensive summary of findings.
- **Logs**:
 - `data/logs/pipeline.log`: Execution logs including timing and errors.
 - `data/logs/tool_validation_log.csv`: Validation status of required tools.

**Note**: The pipeline may take several hours to complete depending on the number of repositories and their size. A timeout of 6 hours is enforced per task execution.

## Verification

To verify the results, inspect `data/results/summary_report.txt` and the generated plots in `data/results/plots/`. Ensure that `unified_metrics.csv` contains non-null values for `total_lines_changed`, `debt_score`, `avg_loc`, and `contributor_count`.