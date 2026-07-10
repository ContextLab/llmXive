# Quickstart: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## Prerequisites
-   Python 3.11+
-   Git
-   Access to NIST Materials Data Repository (for data fetching)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-393-predicting-the-influence-of-composition-/code
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

## Data Preparation
*Note: The pipeline expects raw data files in `data/raw/`. If running locally for the first time, you may need to manually download sample data or run the ingestion script if configured with API keys.*

1.  **Run the ingestion script** (if API access is configured):
    ```bash
    python -m src.ingestion.fetch_nist
    python -m src.ingestion.fetch_journal_data
    ```
    *Alternatively, place downloaded CSV/JSON files manually into `data/raw/`.*

2.  **Verify data presence**:
    Ensure `data/raw/` contains at least one file from each source type (NIST, Journal, Manual).

## Running the Pipeline

Execute the full pipeline (Ingestion -> Preprocessing -> Feature Engineering -> Training -> Validation):

```bash
python main.py
```

This will:
1.  Standardize units and filter DFT data.
2.  Compute 5 composition descriptors.
3.  Train Linear and Random Forest models with 5-fold CV.
4.  Perform F-tests and bootstrapping.
5.  Generate reports in `docs/reports/`.

## Expected Outputs
-   `data/processed/alloys_features.csv`: The final dataset used for modeling.
-   `models/`: Pickled model artifacts.
-   `docs/reports/metrics.json`: Numerical results (R², MAE, p-values).
-   `docs/reports/pdp_coercivity.png`: Partial dependence plots.
-   `docs/reports/statistical_limitations.md`: Explicit statement on model limitations.

## Troubleshooting
-   **Error: "Missing elemental property"**: Ensure `data/raw/elemental_properties.csv` is present and matches the `code/src/utils/periodic_table.py` format.
-   **Warning: "Dataset size < 50"**: The pipeline will continue, but the final report will flag low statistical power.
-   **Error: "DFT data found"**: This is expected. The pipeline filters these out. If *all* data is DFT, the process will fail with a "Data Scarcity Warning" as per **FR-008**.
