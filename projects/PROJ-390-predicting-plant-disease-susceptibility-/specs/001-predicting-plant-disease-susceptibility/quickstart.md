# Quickstart: Predicting Plant Disease Susceptibility

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local equivalent with 7GB+ RAM).
*   (Optional) NCBI API key for higher rate limits.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
    git checkout 001-plant-disease-susceptibility
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This includes `pysam`, `scikit-learn` (with KNNImputer), `pandas`, `requests`, and `minimap2` (via subprocess).*

4.  **Install System Tools** (if running locally):
    *   Ensure `minimap2` and `bcftools` are installed and in your PATH.
    *   On Ubuntu: `sudo apt-get install minimap2 bcftools`

## Running the Pipeline

The pipeline is designed to run end-to-end.

### 1. Feasibility Gate & Label Validation
*Note: This step checks for real data. If not found, the project halts.*

```bash
python src/ingestion/feasibility_gate.py --config config.yaml
# If PASS, proceed. If FAIL, review feasibility_report.md.
```

### 2. Download Data (Ingestion)
*Note: If real data is found, this step downloads it. If not, synthetic data is generated for schema testing ONLY.*

```bash
python src/ingestion/download_sra.py --config config.yaml
python src/ingestion/align_and_call.py --input data/raw/
python src/ingestion/merge_features.py --output data/processed/feature_matrix.csv --imputation_method knn
```

### 3. Dimensionality Reduction
```bash
python src/modeling/reduce_dimensions.py --input data/processed/feature_matrix.csv --output data/processed/reduced_matrix.csv
```

### 4. Train Models
```bash
python src/modeling/train_models.py --input data/processed/reduced_matrix.csv --output models/
```

### 5. Validate & Evaluate
```bash
python src/modeling/evaluate.py --model models/random_forest.pkl --input data/processed/reduced_matrix.csv
python src/modeling/validation.py --model models/random_forest.pkl --permutations 1000
python src/modeling/variance_decomposition.py --model models/random_forest.pkl --input data/processed/reduced_matrix.csv
```

### 6. View Results
*   **Performance Report**: `results/model_performance.json`
*   **Feature Importance**: `results/feature_importance.csv`
*   **Variance Decomposition**: `results/variance_decomposition.json`
*   **Plots**: `results/pr_curve.png`, `results/sensitivity_analysis.png`

## Troubleshooting

*   **Feasibility Gate Failed**: If `feasibility_gate.py` returns FAIL, review `feasibility_report.md`. The project may need to be reframed as "Pipeline Validation" only.
*   **NCBI Rate Limit**: The script automatically retries with exponential backoff. If it fails after 3 retries, it logs the error and skips the sample.
*   **Missing Environmental Data**: If ERA5/NOAA data is missing, the system uses **k-NN** imputation. If no neighbors exist, the sample is excluded and logged.
*   **RAM Error**: If the process exceeds 7GB RAM, reduce the sample size in `config.yaml` (e.g., `max_samples: 500`).

## Verification

Run the test suite to verify the pipeline:
```bash
pytest tests/
```
Expected output:
*   `feature_matrix.csv` exists with no NaN values.
*   `model_performance.json` contains AUC-ROC with 95% CI.
*   `p-value` from permutation test is reported (if real data was used).
*   `variance_decomposition.json` exists with genomic vs. environmental breakdown.