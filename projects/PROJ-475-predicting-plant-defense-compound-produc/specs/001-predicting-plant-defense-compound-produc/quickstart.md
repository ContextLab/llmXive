# Quickstart: Predicting Plant Defense Compound Production

## Prerequisites

-   Python 3.11+
-   `pip`
-   14GB+ free disk space (for temporary data)
-   7GB+ RAM

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-475-predicting-plant-defense-compound-produc
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

1.  **Execute the full pipeline**:
    ```bash
    python code/main.py
    ```
    This runs:
    -   Data Ingestion (Mock generation fallback if no verified URL)
    -   Validation & Merging
    -   Feature Engineering (including PCA for structure control)
    -   Model Training (LASSO)
    -   Statistical Validation (Permutation, Sensitivity)

2.  **Check outputs**:
    -   Processed data: `data/processed/merged_features.csv`
    -   Model results: `data/processed/model_results.json`
    -   Plots: `data/processed/plots/`

## Testing

Run the test suite to verify functionality:

```bash
pytest tests/
```

Specific tests:
-   `tests/test_ingestion.py`: Verifies mock data generation and schema.
-   `tests/test_models.py`: Verifies LASSO training and CV logic.
-   `tests/test_stats.py`: Verifies permutation test and BH correction.

## Troubleshooting

-   **Memory Error**: If `MemoryError` occurs, reduce the number of synthetic SNPs in `config.py` or increase the RAM limit (not possible on free-tier).
-   **Disk Full**: Ensure 14GB free space. The pipeline cleans up intermediate VCF files after aggregation.
-   **No Verified Data**: The pipeline defaults to mock data. To use real data, update `data/ingestion.py` to point to valid URLs (once verified).