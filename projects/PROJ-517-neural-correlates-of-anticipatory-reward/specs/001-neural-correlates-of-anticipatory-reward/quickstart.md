# Quickstart: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

## Prerequisites
*   Python 3.10+
*   `pip` or `conda`
*   Access to the project repository.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-517-neural-correlates-of-anticipatory-reward
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

## Data Setup

### Option A: Real Data (Production)
1.  Ensure the dataset is downloaded to `data/raw/`.
2.  Verify the file matches `contracts/dataset.schema.yaml`.
    ```bash
    python -m tests.contract.test_schemas
    ```

### Option B: Synthetic Data (CI/Development)
1.  Generate synthetic test data:
    ```bash
    python code/synthetic_generator.py --output data/raw/synthetic_test.csv
    ```
2.  This creates a file compatible with the ingestion pipeline for testing.

## Running the Pipeline

Execute the full pipeline (Ingestion -> Modeling -> Visualization -> Reporting):

```bash
python code/run_pipeline.py --data data/raw/synthetic_test.csv --output data/processed/
```

**Expected Output**:
*   `data/processed/unified_data.csv`
*   `data/processed/spike_sorting_validation_report.md`
*   `data/processed/summary_report.txt`
*   `data/figures/firing_rate_vs_reward.png`

## Running Tests

1.  **Unit Tests**:
    ```bash
    pytest tests/unit/ -v
    ```
    *Specifically tests permutation logic (`test_modeling_permutation.py`).*

2.  **Integration Tests**:
    ```bash
    pytest tests/integration/ -v
    ```
    *Tests the full ingestion pipeline with synthetic data.*

3.  **Contract Tests**:
    ```bash
    pytest tests/contract/ -v
    ```
    *Validates data against schemas.*

## Troubleshooting

*   **Memory Error**: If processing large datasets, ensure `streaming=True` is used in the ingestion script (if implemented) or reduce the dataset size.
*   **Schema Mismatch**: Verify `data/raw/*.csv` columns match `contracts/dataset.schema.yaml`.
*   **Missing Spike Sorting Metadata**: If the dataset lacks `spike_sorting_metadata`, the pipeline will flag `valid_spike_sorting=False` and log a warning, and halt the causal claim.
