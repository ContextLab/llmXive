# Quickstart: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Prerequisites

-   Python 3.11+
-   Git
-   GitHub Actions (for CI execution) or local environment for testing.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-264-assessing-the-stability-of-statistical-m
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
    *Dependencies*: `pandas`, `numpy`, `scikit-learn`, `scipy`, `openml`, `requests`, `pyyaml`, `pytest`.

## Running the Pipeline

### 1. Data Preparation (Caching)
The pipeline automatically downloads and caches datasets if they are not present in `data/raw/`.
To force a refresh or validate checksums:
```bash
python code/dataset_loader.py --validate
```

### 2. Execute Evaluation
Run the full repeated cross-validation and analysis pipeline:
```bash
python code/main.py
```
This will:
-   Select multiple binary classification datasets (varying sample sizes).
-   Run multiple repeats for 3 models.
-   Calculate CV, correlations, and permutation tests.
-   Save results to `results/`.

### 3. Verify Results
Check the generated reports:
```bash
cat results/statistical_tests.json
```

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v
```

## Troubleshooting

-   **Runtime Error**: If the pipeline exceeds 6 hours, reduce `n_estimators` in `code/config.py` or the number of repeats.
-   **Memory Error**: Ensure large datasets are not loaded simultaneously. The code processes them sequentially.
-   **Missing Datasets**: If the `openml` API is unreachable, check network connectivity. The pipeline is designed to skip failed downloads and continue with remaining datasets.
