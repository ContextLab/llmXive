# Quickstart: Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

## Prerequisites
*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI execution) or a local environment with 8GB+ RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-285-assessing-the-impact-of-data-filtering-o
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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CI runners.*

## Running the Pipeline

### 1. Generate/Load Data
Run the data loader to fetch the verified SLFC dataset.
```bash
python code/data_loader.py --load-slfc
```
*This creates `data/raw/slfc_dataset.parquet` and `data/raw/injection_ground_truth.csv`.*

### 2. Execute Filtering & Validation
Run the main analysis pipeline.
```bash
python code/main.py
```
*This executes:*
*   *Grid filtering (SNR 5-20, Morph 0.3-0.9)*
*   *Coordinate matching and purity calculation (using real SLFC labels)*
*   *Cumulative Link Model (CLM) and Bootstrap analysis of Recovery Rate*
*   *Sensitivity sweep*

### 3. Generate Visualizations
```bash
python code/visualization.py
```
*Outputs plots to `data/processed/plots/`.*

## Verifying Results

1.  **Check Detection Matrix**:
    ```bash
    head data/processed/detection_matrix.csv
    ```
    *Verify a set of rows corresponding to the combinations of SNR and Morph categories.

The research question is: How does the method perform across different SNR and Morph configurations?
The method is: Systematic verification of data rows across the defined parameter space.
References: [Insert DOI/arXiv/author-year here]*

2.  **Check Sensitivity Report**:
    ```bash
    cat data/processed/sensitivity_sweep.csv
    ```
    *Verify `fp_variation` column exists.*

3.  **Check Injection Recovery**:
    ```bash
    cat data/processed/injection_recovery_report.json
    ```
    *Verify `"threshold_met": true` and `"recovery_rate": >= 0.95`.*

4.  **Check Memory Profile**:
    ```bash
    cat data/processed/memory_profile.csv
    ```
    *Verify peak memory usage is within limits.*

## Troubleshooting

*   **Memory Error**: Ensure `data_loader.py` is using chunked reading. If running locally, try reducing the dataset size in `config.py`.
*   **Missing Columns**: If `SNR` or `morphology_score` are missing, the SLFC extraction logic may have failed. Check `data/raw/slfc_dataset.parquet` schema.
*   **Coordinate Mismatch**: If validation fails, check that RA/Dec are in degrees and tolerance is set to 1.0 arcsec.
