# Quickstart: Statistical Analysis of Algorithmic Fairness Metrics

## Prerequisites

- Python 3.11+
- pip
- git

## Setup

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd <repo-name>
    ```

2.  **Install Dependencies**:
    ```bash
    cd code
    pip install -r requirements.txt
    ```

3.  **Verify Environment**:
    ```bash
    python -c "import pandas, sklearn, statsmodels; print('OK')"
    ```

## Run Pipeline

1.  **Download Data**:
    ```bash
    python download/download_datasets.py
    ```
    *Outputs: `data/raw/*.csv`*

2.  **Preprocess**:
    ```bash
    python preprocess/preprocess_data.py
    ```
    *Outputs: `data/processed/*.parquet`*

3.  **Analyze**:
    ```bash
    python analysis/train_models.py
    python analysis/compute_metrics.py
    python analysis/regression_analysis.py
    python analysis/bootstrap_analysis.py
    ```
    *Outputs: `data/analysis/*.csv`*

4.  **Visualize**:
    ```bash
    python viz/generate_plots.py
    ```
    *Outputs: `data/analysis/figures/*.png`*

5.  **Run Tests**:
    ```bash
    pytest tests/
    ```

## Troubleshooting

- **Memory Error**: Ensure data sampling (≤100k rows) is active in `preprocess_data.py`. Check `data/analysis/logs/memory.log` for peak usage.
- **Missing Protected Attribute**: Check logs in `data/processed/logs/` for skipped datasets. Verify dataset meets binary protected attribute requirement.
- **Dataset Limitation**: If <5 suitable datasets found, check `data/processed/logs/dataset_constraint.log` for documentation. Analysis will proceed with available datasets.
- **GPU Detected**: Ensure no CUDA flags are set; library versions must support CPU-only execution.
- **Metric Calculation Failed**: Check `data/processed/logs/metric_errors.log` for failure_reason entries. Common causes: zero predictions for a class, class imbalance extreme.

## Output Locations

- **Metrics**: `data/analysis/metrics.csv`
- **Correlations**: `data/analysis/correlations.csv`
- **Regression**: `data/analysis/regression.csv`
- **Bootstrap CIs**: `data/analysis/bootstrap_ci.csv`
- **Figures**: `data/analysis/figures/`
- **Logs**: `data/processed/logs/`, `data/analysis/logs/`
