# Quickstart: GitHub Issue Resolution Analysis

## Prerequisites

- Python 3.11+
- `pip`
- Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-208-statistical-analysis-of-publicly-availab
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Key dependencies*: `pandas`, `scipy`, `statsmodels`, `datasets`, `seaborn`, `matplotlib`.

3.  **Verify Data Access**:
    Ensure you can access HuggingFace datasets (no auth required for public datasets).
    ```python
    from datasets import load_dataset
    ds = load_dataset("akhousker/github-issues", split="train")
    print(f"Loaded {len(ds)} records")
    ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

### What happens?
1.  **Data Loading**: Streams data from HuggingFace, filters closed issues.
2.  **Cleaning**: Calculates resolution times, flags outliers (>30 days), excludes invalid timestamps.
3.  **Distribution Analysis**: Fits Log-Normal and Weibull models; generates ECDF plots.
4.  **Hypothesis Testing**: Runs Kruskal-Wallis/ANOVA with Holm-Bonferroni correction.
5.  **Mixed-Effects Modeling**: Fits LMM with repository random intercepts; performs **10-Fold CV**.
6.  **Sensitivity Analysis**: Sweeps thresholds {0.01, 0.05, 0.1}.
7.  **Output**: Generates `data/processed/cleaned_issues.csv`, figures, and JSON reports.

## Output Artifacts

- `data/processed/cleaned_issues.csv`: The analysis-ready dataset.
- `data/interim/distribution_metrics.json`: KS, p-values, AIC for fitted models.
- `data/interim/hypothesis_results.json`: P-values, adjusted p-values, effect sizes.
- `data/interim/mixed_effects_results.json`: MAE, R² from **10-Fold CV**.
- `figures/`: ECDF plots, histograms (with "associational" captions).

## Validation

Run the test suite to verify data integrity and statistical logic:

```bash
pytest tests/
```

Specific checks:
- **T014**: Verifies `cleaned_issues.csv` exists and has ≥1000 rows (Blocking Gate).
- **T016**: Verifies Log-Normal/Weibull fit metrics are present.
- **T025**: Verifies **10-Fold CV** MAE/R² are calculated.