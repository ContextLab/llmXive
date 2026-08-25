# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

-   Python 3.11+
-   Git
-   Access to `materialsproject.org` API (optional, if NIST data is insufficient)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-420-predicting-the-effect-of-alloying-on-the
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the main entry point. It handles data fetching, cleaning, modeling, and reporting.

```bash
python code/main.py
```

### Expected Output

Upon successful completion, the following files will be generated:

-   `data/raw/`: Raw downloaded data files.
-   `data/processed/alloy_cleaned.csv`: Filtered and normalized dataset.
-   `models/rf_model.pkl`: Trained Random Forest model.
-   `data/processed/model_metrics.json`: CV and Test MAE.
-   `data/processed/collinearity_diagnostic.json`: VIF analysis.
-   `results/feature_importance_summary.json`: Ranked elements.
-   `results/final_report.md`: The final scientific report.

## Verification

To verify the results and ensure reproducibility:

```bash
pytest tests/
```

This runs contract tests against the generated JSON schemas and unit tests for the ILR transformation.

## Troubleshooting

-   **Error: "No verified open-source dataset found"**: The pipeline could not fetch data from NIST or Materials Project. Check your internet connection or API keys.
-   **Error: "Insufficient data (< 50 samples)"**: The filtered dataset is too small for 5-fold cross-validation. The pipeline halts to prevent unreliable results.
-   **Error: "Unit conversion failed"**: The raw data contained inconsistent units (e.g., MPa vs GPa) that could not be resolved automatically. Check `data/processed/exclusion_log.csv`.
