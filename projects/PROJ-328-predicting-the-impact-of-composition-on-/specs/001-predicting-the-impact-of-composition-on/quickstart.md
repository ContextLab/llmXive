# Quickstart: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

## Prerequisites

*   Python 3.11+
*   Git
*   Access to literature PDFs (for data ingestion, as no public API is verified).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-328-predicting-the-impact-of-composition-on-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

The pipeline relies exclusively on the 'Literature Aggregator' processing the 'Verified Literature Corpus'.

1.  **Prepare Raw Data**: Place the specific PDFs from the 'Verified Literature Corpus' (e.g., the Mg-Gd paper, standard Sn-Ag-Cu reviews) in `data/raw/pdfs/`.
2.  **Run Aggregator**: Execute `python code/ingestion/aggregator.py` to scrape the PDFs and generate `data/raw/solder_raw.csv`.
    *   *Note*: The aggregator enforces a strict schema check (element sum, hardness unit). Records failing this check are dropped.
3.  **Verify**: Check `data/raw/solder_raw.csv` for completeness. If N < 50, the pipeline will emit an 'Exploratory' warning.

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/run_pipeline.py
```

This script performs:
1.  **Ingestion**: Loads and validates `data/raw/solder_raw.csv`.
2.  **Feature Engineering**: Applies CLR transform and computes descriptors.
3.  **Model Training**: Trains XGBoost and Linear Regression (5-fold CV).
4.  **Evaluation**: Computes R², RMSE, Bootstrap CIs, VIF, SHAP, and Sensitivity Analysis.
5.  **Visualization**: Generates `data/outputs/` plots.

## Verifying Results

Check `data/outputs/report.md` for:
*   **Dataset Size**: Confirm N ≥ 50 (warning if N < 100).
*   **Model Comparison**: Bootstrap Model Comparison p-value.
*   **Top Features**: SHAP ranking.
*   **Collinearity**: VIF scores (flag if ≥ 5).
*   **Sensitivity**: Fraction of bootstrap samples exceeding R² thresholds {0.3, 0.5, 0.6, 0.7}.

## Troubleshooting

*   **Error: "Data volume below target"**: The pipeline found < 50 records. The study is declared 'Exploratory'.
*   **Error: "Composition sum < 95%"**: Check the PDFs for missing elements or rounding errors.
*   **Memory Error**: Unlikely on this dataset size, but ensure no GPU libraries are installed.
