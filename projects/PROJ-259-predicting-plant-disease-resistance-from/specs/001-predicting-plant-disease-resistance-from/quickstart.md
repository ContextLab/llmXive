# Quickstart: Predict Plant Disease Resistance from Multi‑omics Data

## Prerequisites

*   Python 3.11+
*   Docker (for `fastp` and `bcftools` integration)
*   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-259-predicting-plant-disease-resistance-from
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Build the Docker container** (optional, recommended for reproducibility):
    ```bash
    docker build -t plant-resistance-pipeline .
    ```

## Running the Pipeline

### 1. Data Preparation
If you have a real dataset, place it in `data/raw/` and update `data/data_manifest.yaml` with the accession numbers and checksums.

**Note**: If no real dataset is available, the pipeline will automatically generate a **synthetic dataset** for demonstration purposes. This is the default mode due to the lack of public matched data.

### 2. Execute the Pipeline
Run the main script:
```bash
python code/main.py --mode full
```

This will:
1.  **Download/Generate Data**: Fetch from NCBI/MetaboLights or generate synthetic data.
2.  **Preprocess**: Call variants, normalize metabolites, align samples.
3.  **Split Data**: Perform stratified splitting (Training/Hold-out).
4.  **Feature Selection**: Run LASSO/RF with sensitivity sweep.
5.  **Model Training**: Train Elastic-Net/GBM with 5-fold CV.
6.  **Validation**: Run permutation testing and VIF diagnostics.
7.  **Output**: Save results to `artifacts/`.

### 3. Verify Results
Check the `artifacts/reports/metrics.json` for performance metrics:
*   `cv_accuracy`: Should be ≥ 0.75 (in Simulation Mode, this validates the pipeline logic).
*   `permutation_p_value`: Should be ≤ 0.05 (in Simulation Mode, this validates signal detection).
*   `feature_stability`: CSV of top features.

### 4. Inspect Biomarkers
View the top selected features:
```bash
cat artifacts/reports/top_features.csv
```

## Troubleshooting

*   **Error: `EX_DATA_INTEGRITY (02)`**: Fewer than 100 paired samples found. Check data quality or use a larger dataset.
*   **Error: `EX_POWER_INSUFFICIENT (03)`**: Sample size < 100. The pipeline requires this for statistical power.
*   **Missing Data**: If the pipeline cannot find real data, it will automatically switch to synthetic mode. Check `data/data_manifest.yaml` for logs.
*   **Note on Results**: If running in Simulation Mode, the reported accuracy and p-values reflect the pipeline's ability to detect the *injected signal* in the synthetic data, not a biological finding about real plant disease.