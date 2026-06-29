# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the Moral Machine dataset (public URL as per spec).
*   A GitHub Actions Free Runner (or local machine with 7 GB+ RAM, 2+ CPU cores).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-545-the-influence-of-visual-salience-on-atte
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

## Data Preparation

1.  **Download the dataset**:
    Run the ingestion script to download and subset the Moral Machine dataset.
    ```bash
    python code/data/ingest.py --subset-size 50000 --seed 42
    ```
    *Output*: `data/raw/moral_machine_subset.csv`

2.  **Compute Salience**:
    Run the salience computation script.
    ```bash
    python code/data/salience.py --input data/raw/moral_machine_subset.csv --output data/processed/salience_enriched.csv
    ```
    *Output*: `data/processed/salience_enriched.csv` (includes `salience_score` column).

## Running the Analysis

1.  **Fit the aDDM Models**:
    Run the grid search and fitting script.
    ```bash
    python code/models/fit.py --input data/processed/salience_enriched.csv --output data/processed/model_fits.json
    ```
    *Note*: This may take up to 30 minutes per fold on a CPU.

2.  **Run Model Comparison & Sensitivity**:
    Run the comparison and sensitivity analysis.
    ```bash
    python code/analysis/compare.py --fits data/processed/model_fits.json --data data/processed/salience_enriched.csv
    ```
    *Output*: `data/processed/comparison_report.csv`

## Verification

To verify the pipeline:
1.  Check that `salience_enriched.csv` has no null values in `salience_score`.
2.  Check that `comparison_report.csv` contains entries for threshold sweeps {0.01, 0.05, 0.10}.
3.  Ensure the VIF diagnostic is present and flags any collinearity > 5.0.

## Troubleshooting

*   **Non-convergence**: If a scenario fails to converge, check `logs/fit.log` for the retry count (capped at 3).
*   **Missing Images**: The script automatically falls back to text heuristics for broken image URLs.
*   **Memory Errors**: Ensure the subset size is ≤ 50,000 rows.
