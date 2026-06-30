# Quickstart: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Prerequisites

*   Python 3.11+
*   R 4.3+
*   Git
*   Access to the Dryad and AnAge datasets (or ability to download them manually if automated fetch fails).

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-055-investigating-the-impact-of-telomere-len
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
    *Note*: This installs `rpy2` and required Python packages. R packages (`phylolm`, `lme4`, `rotl`) are installed via `renv` or manually in the R environment.

## Data Setup

The pipeline expects raw data in `data/raw/`.

1.  **Run Data Discovery**:
    ```bash
    python code/01_discover_data.py
    ```
    *Checks*: Verify that specific Dryad dataset IDs are identified and logged. If this fails, the pipeline will not proceed.

2.  **Download Data**:
    *   If automated fetch works, it will populate `data/raw/`.
    *   If manual download is required, place the specific Dryad CSVs and AnAge CSVs in `data/raw/`.

3.  **Download Phylogeny**:
    *   The pipeline will automatically fetch the Jetz et al. (2012) tree via `rotl` during the modeling phase. No manual download required if `rotl` is installed in R.

## Running the Pipeline

Execute the full pipeline in order:

1.  **Ingest and Clean**:
    ```bash
    python code/02_ingest_data.py
    python code/03_clean_merge.py
    ```
    *Checks*: Verify `data/processed/merged_analysis.csv` exists and contains >15 species (or check logs for low power warning).

2.  **Modeling**:
    ```bash
    python code/04_model_pglS.py
    ```
    *Checks*: Verify `results/model_summary.csv` and `results/association_forest.png` exist.

3.  **Sensitivity Analysis**:
    ```bash
    python code/04_sensitivity.py
    ```
    *Checks*: Verify `results/sensitivity_log.csv`.

4.  **Visualization**:
    ```bash
    python code/05_visualize.py
    ```
    *Checks*: Verify `results/moderator_plot.png`.

## Verification

*   **Data Integrity**: Run `python code/utils.py --verify-checksums` to ensure raw data hasn't changed.
*   **Reproducibility**: Re-run the entire pipeline. Compare the checksums of `results/` files. They should match the previous run (given fixed seeds).
*   **State Check**: Verify `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml` has been updated with new artifact hashes.

## Troubleshooting

*   **"Low Power" Error**: If the merged dataset has < 15 species, the PGLS model will run with fixed lambda and a warning. Check your data sources for more species.
*   **Memory Error**: If you encounter OOM errors, check that you are not loading the full raw datasets into memory at once. The scripts use chunked processing if needed.
*   **Missing Units**: If many records are excluded due to unit issues, verify that the Dryad metadata includes conversion factors.
*   **R Package Errors**: Ensure R packages (`phylolm`, `rotl`) are installed in the R environment accessible to `rpy2`.