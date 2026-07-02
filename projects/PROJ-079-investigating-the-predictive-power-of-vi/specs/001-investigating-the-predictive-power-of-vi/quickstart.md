# Quickstart: Predictive Modeling of Host Immune Response from Viral Sequence Features

## Prerequisites

-   **Python**: 3.11+
-   **System**: Linux (Ubuntu 20.04+ recommended).
-   **R Environment**: R (>= 4.0) must be installed and accessible in the PATH. This is required for `edgeR` TMM normalization via `rpy2`.
-   **Dependencies**: `conda` or `pip` (pinned versions in `requirements.txt`).
-   **Network**: Internet access for downloading NCBI Virus and GEO data.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-079-investigating-the-predictive-power-of-vi
    ```

2.  **Create and activate environment**:
    ```bash
    conda create -n immune-predict python=3.11 r-base=4.2
    conda activate immune-predict
    pip install -r requirements.txt
    ```

3.  **Install R Packages**:
    The pipeline requires the `edgeR` package for TMM normalization. Install it within the R environment:
    ```bash
    R -e "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager'); BiocManager::install('edgeR')"
    ```

4.  **Verify dependencies**:
    ```bash
    python -c "import biopython; import sklearn; import rpy2; print('OK')"
    ```

## Configuration

Before running the pipeline, ensure the `config/studies.yaml` file exists. Since the "Verified datasets" block does not contain the specific GEO/NCBI data, you must define the study scope here.

**Example `config/studies.yaml`**:
```yaml
studies:
  - geo_series: "GSE12345"  # Replace with actual study ID
    virus_accessions:
      - "NC_000001"
      - "NC_000002"
  - geo_series: "GSE67890"
    virus_accessions:
      - "NC_000003"
```

*Note: If you do not have specific studies, the pipeline will attempt to fetch a default set if configured in `src/utils/config.py`, but manual specification is recommended for reproducibility.*

## Running the Pipeline

Execute the full pipeline:

```bash
python src/main.py --config config/studies.yaml
```

**Expected Output**:
-   `data/raw/`: Downloaded FASTA and GEO matrices.
-   `data/processed/feature_matrix.csv`: Merged dataset.
-   `data/artifacts/metrics.json`: R², RMSE, p-values.
-   `data/artifacts/plots/`: Feature importance and partial dependence plots.

## Verification

1.  **Check Data Existence**:
    ```bash
    ls -lh data/processed/feature_matrix.csv
    ```
2.  **Check Metrics**:
    ```bash
    cat data/artifacts/metrics.json
    # Should contain: {"r2": 0.30, "rmse": 0.15, "min_p":,...}
    ```
3.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/ -v
    ```

## Troubleshooting

-   **"No genomes found"**: Ensure `config/studies.yaml` has valid NCBI accessions.
-   **"Runtime exceeded 4 hours"**: The Uniform Stability Proxy is used. If still too slow, reduce the number of k-mers or samples in `config/studies.yaml`.
-   **"Insufficient samples"**: The pipeline aborts if <30 samples or <5 test strains are found. Expand `config/studies.yaml`.
-   **"edgeR not found"**: Ensure R is installed and the `edgeR` package was installed via the `R -e` command in the Installation steps.