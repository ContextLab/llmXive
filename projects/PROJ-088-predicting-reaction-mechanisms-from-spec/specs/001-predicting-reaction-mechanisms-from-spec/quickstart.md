# Quickstart: Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning

## Prerequisites

-   Python 3.11+
-   pip (Python package installer)
-   Git (for cloning the repository)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd projects/PROJ-088-predicting-reaction-mechanisms-from-spec
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

## Running the Pipeline

The pipeline is executed via the CLI entry point.

1.  **Run the full pipeline**:
    This command performs ingestion, preprocessing, training, and analysis.
    ```bash
    python -m src.cli.main run --seed 42 --max-rows 5000
    ```

2.  **Run specific stages** (for debugging):
    -   **Ingestion only**:
        ```bash
        python -m src.cli.main ingest
        ```
    -   **Training only** (requires pre-processed data):
        ```bash
        python -m src.cli.modeling train
        ```
    -   **Analysis only** (requires trained models):
        ```bash
        python -m src.cli.analysis run
        ```

## Output Artifacts

After a successful run, the following files will be generated in `data/processed/`:

-   `fingerprints.parquet`: The standardized 512-bin dataset.
-   `model_metrics.json`: Accuracy, F1, and p-values.
-   `feature_importance.csv`: Ranked list of spectral bins.
-   `report.md`: The final summary report.

## Verification

To verify the results:

1.  **Check Class Balance**:
    Ensure no class has a sufficient number of samples for robust analysis.
    ```bash
    python -m src.utils.io check_balance data/processed/fingerprints.parquet
    ```

2.  **Verify Significance**:
    Confirm the permutation p-value is reported.
    ```bash
    python -m src.utils.io check_significance data/processed/model_metrics.json
    ```

3.  **Run Tests**:
    Execute the contract and unit tests.
    ```bash
    pytest tests/
    ```
