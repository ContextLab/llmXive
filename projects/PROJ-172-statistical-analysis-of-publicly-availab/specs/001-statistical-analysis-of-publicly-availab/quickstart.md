# Quickstart: Statistical Analysis of Publicly Available Sports Data for Predictive Modeling

## 1. Prerequisites

- Python 3.10+
- pip
- Git

## 2. Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs `xgboost` (CPU version), `scikit-learn`, `pandas`, `statsmodels`, and `pytest`.*

## 3. Data Setup

The pipeline handles data automatically.
- **Option A (Real Data)**: If the environment has network access and Retrosheet/BR are reachable, the script will attempt to download.
- **Option B (Synthetic Fallback)**: If downloads fail (or in CI), the script will generate a synthetic dataset with realistic MLB statistics.

Run the data preparation script:
```bash
python code/main.py --step prepare_data
```
*This creates `data/processed/features.csv`, `train.csv`, and `test.csv`.*

## 4. Running the Pipeline

Execute the full pipeline (Training, Evaluation, Significance Testing):
```bash
python code/main.py --step full_run
```

**Output**:
- `artifacts/reports/final_results.json`: Contains ROC-AUC, Log-Loss, Brier scores, and p-values.
- `artifacts/figures/sensitivity_analysis.png`: Threshold sweep plot.
- `artifacts/reports/methodology_report.md`: Summary of statistical validity.

## 5. Running Tests

Ensure the temporal split and feature engineering logic are correct:
```bash
pytest tests/ -v
```

## 6. Troubleshooting

- **Memory Error**: If running out of RAM (7GB limit), the pipeline automatically down-samples the synthetic data. If using real data, ensure the dataset is filtered to the 2000-2022 range before loading.
- **Missing Dependencies**: Ensure `xgboost` is the CPU version. Do not install `bitsandbytes` or CUDA-specific packages.
