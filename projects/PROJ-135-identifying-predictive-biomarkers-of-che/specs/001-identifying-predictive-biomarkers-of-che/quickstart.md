# Quickstart: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Prerequisites

-   Python 3.11+
-   R (for DESeq2 via `rpy2`)
-   Git
-   Access to GitHub Actions (for CI execution)

## Installation

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd PROJ-135-identifying-predictive-biomarkers-of-che
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure R and `rpy2` are compatible.*

4.  **Verify R Installation**:
    ```bash
    R --version
    Rscript -e "if (!requireNamespace('DESeq2', quietly = TRUE)) install.packages('DESeq2', repos='https://cloud.r-project.org')"
    ```

## Running the Pipeline

### 1. Data Acquisition
```bash
python src/data_acquisition.py
```
-   Downloads TCGA and GEO data to `data/raw/`.
-   Logs warnings if size > 5GB.

### 2. Preprocessing
```bash
python src/preprocessing.py
```
-   Harmonizes gene IDs.
-   Filters low-expression genes.
-   Applies VST (TCGA) / RMA (GEO) and batch correction (ComBat with response covariate).
-   Outputs to `data/processed/`.

### 3. Differential Expression & Meta-Analysis
```bash
python src/differential_expression.py
python src/meta_analysis.py
```
-   Runs DESeq2 Wald test.
-   Performs **DerSimonian-Laird Random-Effects Meta-Analysis**.
-   Outputs `results/meta_analysis/gene_panel.json`.

### 4. Modeling & Validation
```bash
python src/modeling.py
python src/validation.py
```
-   Trains elastic-net models.
-   Performs **Nested LOO** (gene selection re-run inside loop) and external validation.
-   Generates `results/summary.md` and plots.

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v
```

Run contract tests:
```bash
pytest tests/contract/ -v
```

## Expected Outputs

-   `data/processed/`: Normalized expression matrices.
-   `results/meta_analysis/gene_panel.json`: Final biomarker panel (Random-Effects derived).
-   `results/summary.md`: Performance metrics and validation results.
-   `results/models/`: Trained model artifacts.

## Troubleshooting

-   **OOM Error**: Reduce sample size in `config.py` or enable streaming.
-   **R Package Missing**: Install `DESeq2` in R as shown above.
-   **Data Download Fail**: Verify internet connection and verified URLs in `research.md`.
