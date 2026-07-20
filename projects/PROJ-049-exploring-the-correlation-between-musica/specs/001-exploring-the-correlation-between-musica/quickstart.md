# Quickstart: Exploring the Correlation Between Musical Preference and Personality Traits

## Prerequisites

*   Python 3.11+
*   `git`
*   Access to the project repository.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-049-exploring-the-correlation-between-musica
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

**Important**: This project requires real data. Do not use synthetic data for analysis.

1.  **Verify Data Availability**:
    The system will attempt to download the required datasets automatically. Ensure you have internet access.
    ```bash
    python code/ingestion.py --check-only
    ```
    *If this fails, the project cannot proceed due to data unavailability (see `research.md`).*

2.  **Download Data**:
    ```bash
    python code/ingestion.py
    ```
    This will create `data/raw/` and `data/processed/merged_users.csv`.

## Running the Analysis

1.  **Execute the full pipeline**:
    ```bash
    python code/analysis.py
    ```
    This script performs:
    *   Data cleaning and merging.
    *   Spearman correlation matrix calculation.
    *   Multiple linear regression with demographic controls.
    *   Benjamini-Hochberg FDR correction.
    *   Visualization generation.

2.  **Verify Outputs**:
    Check the `results/` directory for:
    *   `correlation_heatmap.png`
    *   `results_report.csv` (Satisfies FR-006; defined by `contracts/results.schema.yaml`)
    *   `analysis_results.csv`

## Validation

1.  **Run Unit Tests**:
    ```bash
    pytest tests/ -v
    ```
    Ensure all tests pass, particularly `test_analysis.py` which validates the FDR correction logic.

2.  **Reproducibility Check**:
    Re-run the pipeline on a clean environment to ensure results are identical (random seeds are pinned).

## Troubleshooting

*   **Dataset Not Found**: If `ingestion.py` fails, check the `research.md` file for the list of verified sources. If the specific datasets are not available, the project is blocked until a verified source is found.
*   **Memory Error**: If the dataset is too large, the script will attempt to stream it. If it fails, reduce the sample size in `code/config.py` (only for testing, not for final results).