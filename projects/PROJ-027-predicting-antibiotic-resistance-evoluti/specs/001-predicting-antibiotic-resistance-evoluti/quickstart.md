# Quickstart: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Prerequisites

- Python 3.11+
- Git
- Docker (optional, for Snippy/ARIBA if system install is complex)
- Access to GitHub Actions (for CI) or a local Linux environment with sufficient RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-027-predicting-antibiotic-resistance-evoluti
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
    *Note: This installs `scikit-learn`, `biopython`, `pandas`, `dendropy`, `statsmodels`, etc. Snippy and ARIBA may require system-level installation (e.g., `apt install snippy ariba` or Docker).*

## Running the Pipeline

The pipeline is executed via `code/main.py`.

### 1. Data Ingestion & Feature Extraction
```bash
python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852
```
*   Downloads ~1000 *E. coli* isolates from the specified BioProject.
*   Runs Snippy and ARIBA.
*   Outputs: `data/processed/feature_matrix.csv`.

### 2. Contract Validation (Mandatory Gate)
```bash
pytest tests/contract/
```
*   Validates that `data/processed/feature_matrix.csv` matches `contracts/feature_matrix.schema.yaml`.
*   **Abort if failed**.

### 3. Model Training
```bash
python code/main.py --stage train --antibiotic ciprofloxacin
```
*   Trains Logistic Regression (L1) and Random Forest.
*   Uses **Phylogenetically-Blocked Cross-Validation**.
*   Excludes canonical resistance genes for ciprofloxacin.
*   Outputs: `data/models/ciprofloxacin_model.pkl`.

### 4. Validation & Significance
```bash
python code/main.py --stage validate --antibiotic ciprofloxacin --permutations [sufficient_permutations]
```
*   Runs **PGLS residual permutation test**.
*   Performs sensitivity analysis.
*   Outputs: `data/results/ciprofloxacin_metrics.json`.

### 5. Versioning
```bash
python code/utils/hash_artifacts.py
```
*   Computes SHA256 hashes for all artifacts.
*   Updates `state/` JSON files.

### 6. Visualization
```bash
python code/main.py --stage viz --antibiotic ciprofloxacin
```
*   Generates ROC curves and feature importance plots.
*   Outputs: `data/figures/roc_ciprofloxacin.png`.

## Verification

Run the full test suite to ensure the pipeline integrity:
```bash
pytest tests/
```
*   **Contract Tests**: Validate that output files match `contracts/*.schema.yaml`.
*   **Unit Tests**: Verify data ingestion and feature extraction logic.

## Troubleshooting

- **OOM Error**: Reduce `--n-isolates` to 500.
- **Snippy Failure**: Ensure the reference genome is correctly specified in `code/utils/config.py`.
- **Network Timeout**: The NCBI fetch may be slow; ensure stable internet connection.
- **Phylogeny Error**: Ensure `dendropy` and `statsmodels` are installed.