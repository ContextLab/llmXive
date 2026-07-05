# Quickstart: Predicting the Impact of Strain Rate on the Yield Strength of Metals

## Prerequisites

*   Python 3.11+
*   `pip` or `conda`
*   (Optional) `git` for cloning the repository

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Data Setup

Since the verified dataset list currently lacks materials science data, the pipeline uses a **Physics-Consistent Simulated Data** generator.

1.  **Generate Simulated Data** (for pipeline validation):
    ```bash
    python code/ingestion/fetchers.py --mode simulated --output data/raw/simulated_tensile.csv
    ```
    *This creates a synthetic dataset with a representative number of records, including yield strength, strain rate, and composition. Grain size is generated with independent noise to prevent perfect correlation with yield strength.*

2.  **(Future) Real Data Fetching**:
    Once verified materials datasets are added to `research.md`, update `code/config.py` with the correct URLs and run:
    ```bash
    python code/ingestion/fetchers.py --mode real
    ```

## Running the Pipeline

Execute the full end-to-end pipeline:

```bash
python code/main.py
```

This script performs:
1.  **Ingestion**: Loads data, standardizes units.
2.  **Preprocessing**: Imputes missing values, validates correlations.
3.  **Modeling**: Trains ML and empirical models.
4.  **Evaluation**: Generates metrics, plots, and statistical tests.

### Output Artifacts

After completion, check the following directories:

*   `data/processed/`: Cleaned and imputed datasets.
*   `results/models/`: Serialized model files (`.pkl`).
*   `results/evaluation/`:
    *   `metrics.json`: R², MAE, RMSE for all models.
    *   `shap_summary.json`: Feature importance rankings.
    *   `plots/`: Partial dependence and error distribution plots.
    *   `statistical_tests.json`: Wilcoxon p-values and sensitivity analysis results.
    *   `baseline_saturation_report.json`: Indicates if empirical baselines are saturated.

## Testing

Run the contract tests to ensure data schema compliance:

```bash
pytest tests/contract/ -v
```

Run unit and integration tests:

```bash
pytest tests/ -v
```

## Troubleshooting

*   **Memory Error**: If `MemoryError` occurs, reduce the mock dataset size in `config.py` or enable chunked processing.
*   **Missing Dependencies**: Ensure you are using Python 3.11. Some libraries (e.g., `scikit-learn`) may require specific versions.
*   **Dataset Not Found**: The pipeline will fail if `data/raw/` is empty. Run the simulated generator if no real data is available.