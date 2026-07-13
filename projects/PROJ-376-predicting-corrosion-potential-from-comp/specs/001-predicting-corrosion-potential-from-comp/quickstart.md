# Quickstart: Predicting Corrosion Potential from Composition and Environment

## Prerequisites

*   Python 3.11+
*   `pip`
*   (Optional) `Materials Project API Key` (Set as `MP_API_KEY` environment variable) - *Not used for primary task.*

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-376-predicting-corrosion-potential-from-comp
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Verify environment**:
    ```bash
    python -c "import sklearn, pandas, numpy; print('All imports successful')"
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Data Ingestion
Downloads and validates data. If the NIST source fails validation, it will **halt** with a `DataInsufficientError`.
*   **CI Mode**: Set `MOCK_DATA=1` to load `tests/fixtures/mock_corpus.json` (a verified mock dataset containing the required schema) for testing without live API calls.
```bash
# Production (requires valid data source)
python code/main.py --step ingest

# CI/Testing (uses mock data)
MOCK_DATA=1 python code/main.py --step ingest
```
*Output*: `data/processed/merged_dataset.parquet`

### Step 2: Preprocessing & Splitting
Cleans data and performs the "Compositional Clustering" split.
```bash
python code/main.py --step split
```
*Output*: `data/processed/train_set.parquet`, `data/processed/test_set.parquet`

### Step 3: Model Training
Trains Random Forest and Gradient Boosting models.
```bash
python code/main.py --step train
```
*Output*: `data/results/model_metrics.json`, saved model artifacts.

### Step 4: Evaluation & Interpretability
Calculates permutation importance (2000 permutations), p-values, and generates plots.
```bash
python code/main.py --step interpret
```
*Output*: `data/results/feature_importance.json`, `data/results/plots/` (PDP images).

## Testing

Run the unit and integration tests to verify data integrity and split logic.
```bash
pytest tests/ -v
```

## Troubleshooting

*   **Error: `DataInsufficientError`**: The verified NIST dataset did not contain the required corrosion schema, or no verified dataset was found. The pipeline has halted. Check `research.md` for the list of verified sources.
*   **Error: `Low Cluster Count`**: The clustering algorithm yielded fewer than 3 distinct clusters. The test set would be statistically insufficient. The pipeline has halted.
*   **Error: `Alloy Family Overlap`**: The split logic detected a cluster in both train and test sets. This should not happen if `split.py` is used correctly. Check the `cluster_id` column for inconsistencies.
*   **Error: `Missing Mock Fixture`**: If `MOCK_DATA=1` is set but `tests/fixtures/mock_corpus.json` is missing, the pipeline will fail. Ensure the mock fixture exists and matches the schema.