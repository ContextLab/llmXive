# Quickstart: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Access to a Linux environment (GitHub Actions runner recommended).

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `pymatgen`, `scikit-learn`, `pandas`, `datasets`, `scipy`.*

## Data Preparation

The pipeline automatically downloads data from the verified HuggingFace source (`hmao/all_apis_for_multiapi`).

1.  **Run Ingestion**:
    ```bash
    python code/data_ingestion.py
    ```
    *Output*: `data/processed/heas_train.csv`, `data/processed/holdout_known.csv`, `data/processed/true_novel.csv`.

2.  **Verify Data**:
    Check `data/processed/` for the presence of the three CSV files. Ensure `num_elements >= 5` in all rows.

## Running the Pipeline

Execute the full pipeline (Feature Engineering -> Training -> Evaluation):

```bash
python code/train_models.py && python code/evaluate.py
```

*This will:*
1.  Calculate descriptors for all datasets.
2.  Train Random Forest and Gradient Boosting models (5-fold CV).
3.  Evaluate on `holdout_known.csv` (Error metrics).
4.  Evaluate on `true_novel.csv` (Uncertainty metrics).
5.  Generate `data/reports/final_report.csv` and `data/reports/metrics_summary.json`.

## Generating the Report

The final report includes:
-   Interpolation $R^2$ (Training).
-   Extrapolation $R^2$ (Hold-out Known).
-   T-test p-value (Error degradation) *if N sufficient*.
-   Spearman correlation (Uncertainty vs. Distance in feature space).
-   Top 100 Novel Candidates ranked by uncertainty.

View the report:
```bash
cat data/reports/final_report.csv
```

## Troubleshooting

-   **`KeyError` in descriptors**: Ensure `pymatgen` is installed and the dataset columns match the expected schema (`elements`, `element_fractions`).
-   **Memory Error**: If the dataset is too large, check `code/data_ingestion.py` for streaming logic. The script should handle datasets > 7GB by sampling or streaming.
-   **API Rate Limit**: The ingestion script includes exponential backoff. If it fails, check network connectivity.

## Expected Outputs

-   `data/processed/heas_train.csv`
-   `data/processed/holdout_known.csv`
-   `data/processed/true_novel.csv`
-   `data/models/random_forest.pkl`
-   `data/models/gradient_boosting.pkl`
-   `data/reports/final_report.csv`
-   `data/reports/metrics_summary.json`