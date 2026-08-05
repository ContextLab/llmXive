# Quickstart: Identifying Predictive Predictive Biomarkers of Chemotherapy Response

## 1. Prerequisites

- Python 3.11+
- R 4.3+ (for `TCGAbiolinks`, `GEOquery`, `DESeq2`)
- Git
- Access to GitHub Actions (for CI execution) or local Linux environment.

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-135-identifying-predictive-biomarkers-of-che
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `rpy2`, `scikit-learn`, `pandas`, `statsmodels`.*

4.  **Install R Dependencies** (if running locally):
    ```r
    Rscript -e 'if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")'
    Rscript -e 'BiocManager::install(c("TCGAbiolinks", "GEOquery", "DESeq2", "limma"))'
    ```

## 3. Running the Pipeline

### Option A: Full Run (GitHub Actions)
The pipeline is designed to run on GitHub Actions. Push to the `001-chemo-biomarker-discovery` branch to trigger the workflow.
- **Time Limit**: ≤ 6 hours.
- **Memory Limit**: ≤ 7 GB RAM.
- **Data**: Automatically fetched from TCGA/GEO APIs.

### Option B: Local Run (Subset)
To run a subset locally (e.g., 2 tumor types):
```bash
python code/main.py --tumor-types BRCA,LUAD --subset-size 500
```
- **`--subset-size`**: Limits samples per tumor type to ensure RAM constraints.
- **`--tumor-types`**: Comma-separated list of TCGA project IDs.

## 4. Expected Outputs

- `data/processed/harmonized_counts.csv`: Normalized expression matrix.
- `results/meta_analysis/gene_panel.csv`: Ranked biomarker panel.
- `results/summary.md`: Final report including fallback flags and performance metrics.
- `results/models/final_model.pkl`: Trained elastic-net model.

## 5. Troubleshooting

- **Missing Response Labels**: If the pipeline halts with `NoValidValidationCohort`, verify that the specified GEO datasets (GSE25055, GSE42752) are accessible and contain response annotations.
- **Memory Error**: Increase `--subset-size` or enable streaming (default).
- **LOO Error**: Ensure at least 3 tumor types are selected. If only 2 are available, the pipeline will halt as per FR-008.
