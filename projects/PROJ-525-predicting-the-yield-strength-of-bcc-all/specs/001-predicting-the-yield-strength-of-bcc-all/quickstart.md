# Quickstart: Predicting Yield Strength of BCC Alloys

## Prerequisites

*   Python 3.11+
*   `pip`
*   Access to a GitHub Actions runner (or local environment with sufficient RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-525-predicting-the-yield-strength-of-bcc-all
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via `main.py` in the `code/` directory.

1.  **Download and Filter Data**:
    ```bash
    python code/ingestion.py
    ```
    *This step attempts to fetch the MPEA dataset, filters for BCC, and saves to `data/processed/filtered_bcc.parquet`. If N < 80, the pipeline halts.*

2.  **Engineer Features**:
    ```bash
    python code/features.py
    ```
    *Calculates descriptors (including electronegativity difference) and ILR transforms. Performs VIF check. Output: `data/processed/features.parquet`.*

3.  **Train and Evaluate Models**:
    ```bash
    python code/modeling.py
    ```
    *Trains RF, GB, Ridge using Repeated 5-Fold CV. Outputs metrics to `data/processed/metrics.json`.*

4.  **Run Full Pipeline (Optional)**:
    ```bash
    python code/main.py
    ```

## Testing

Run the test suite to verify feature engineering and pipeline logic:

```bash
pytest tests/
```

## Expected Outputs

*   `data/processed/filtered_bcc.parquet`: Cleaned dataset.
*   `data/processed/features.parquet`: Dataset with engineered features.
*   `data/processed/metrics.json`: Model performance comparison.
*   `logs/rejected_entries.log`: Entries excluded due to missing data or non-BCC structure.
*   `state/artifact_hashes.yaml`: SHA256 checksums for all outputs.
