# Quickstart: Predicting Molecular Packing Efficiency

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient free disk space (for dataset and dependencies)
-   Internet access (to download datasets and models)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-511-predicting-molecular-packing-efficiency-/
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

The pipeline is executed via a single entry point script.

1.  **Run the full pipeline**:
    ```bash
    python code/run_pipeline.py
    ```
    This script performs the following steps in order:
    -   Downloads and filters the COD dataset (official source).
    -   Generates SMILES **from 2D connectivity graphs** (strictly avoiding leakage from experimental 3D coordinates).
    -   Computes 3D descriptors **from experimental CIF coordinates**.
    -   Trains the baseline geometry model and the full topology+geometry model.
    -   Runs a permutation test with a sufficient number of shuffles to ensure stable p-value estimation.
    -   Generates the HTML report.

2.  **Output Locations**:
    -   Raw Data: `data/raw/`
    -   Processed Data: `data/processed/dataset.csv`
    -   Model: `results/model.pt`
    -   Report: `results/report.html`
    -   Metrics: `results/validation_report.md`

## Verification

To verify the results:

1.  **Check Dataset Size**:
    ```bash
    wc -l data/processed/dataset.csv
    # Should be >= 501 (including header)
    ```

2.  **Check Metrics**:
    Open `results/validation_report.md` and verify:
    -   Pearson $r \ge 0.4$ (or $r < 0.2$ with $p \ge 0.05$).
    -   Permutation test with statistical significance (Bonferroni corrected).
    -   VIF diagnostics (no values > 5, or flagged).
    -   Incremental $R^2$ (SMILES contribution) is reported.
    -   Partial correlation controlling for elemental composition is reported.

3.  **Reproducibility**:
    ```bash
    # Run again to ensure identical results (due to pinned seeds)
    python code/run_pipeline.py
    # Compare checksums of results/model.pt and results/validation_report.md
    ```

## Troubleshooting

-   **Runtime Error: "Not enough records"**: The COD filter returned <500 valid entries. Check `data/raw/download.log` for filtering statistics.
-   **Memory Error**: Ensure you are not loading the full COD dump. The script uses streaming. If local memory is <7 GB, reduce `MAX_RECORDS` in `code/config.py`.
-   **SMILES Generation Failed**: Check `data/processed/dataset.csv` for rows where `smiles_source` is "generated" but the SMILES string is empty. These rows are excluded.
-   **2D-Only Entries**: The pipeline excludes 2D-only entries without valid SMILES. If the dataset is too small, this may be the cause.