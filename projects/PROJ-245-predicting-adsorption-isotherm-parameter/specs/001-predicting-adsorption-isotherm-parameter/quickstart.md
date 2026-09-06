# Quickstart: Predicting Adsorption Isotherm Parameters from Molecular Features

## Prerequisites
*   Python 3.11+
*   `pip`
*   Access to the `data/` directory (or permission to run `code/data/fetch.py`).

## Installation
1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-245-predicting-adsorption-isotherm-parameter/code
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import rdkit; import shap; import sklearn; print('All dependencies OK')"
    ```

## Running the Pipeline

### Step 1: Data Fetch & Curation
*Note: The pipeline uses the verified `matsci/qmof` dataset.*
```bash
python code/data/fetch.py
python code/data/preprocessing.py --target henry_constant
```
*This generates `data/processed/target_filtered.parquet`.*

### Step 2: Descriptor Calculation & Imputation
```bash
python code/data/descriptors.py
python code/data/imputation.py
```
*Generates `data/processed/imputed_dataset.parquet` and `data/validation/exclusion_log.json`.*
*Also generates `data/validation/missing_descriptors_report.json`.*

### Step 3: Model Training & Evaluation
```bash
python code/models/train.py --target henry_constant --models linear rf gb
python code/models/null_model.py --target henry_constant
```
*Generates `data/results/model_metrics.json`, `data/results/null_model_fold_rmses.json`, and `data/results/null_model_comparison.json`.*

### Step 4: Interpretation & Reporting
```bash
python code/interpret/shap_analysis.py --model rf
python code/interpret/permutation.py --cluster-by adsorbent_id
python code/interpret/consensus.py
```
*Generates `data/results/shap_summary.json`, `data/results/reduced_model_metrics.json`, `data/results/null_model_top3_rmses.json`, and the final report.*

### Step 5: Runtime Logging
The pipeline automatically generates `data/benchmarks/runtime_log.json` upon completion.

## Validation
To verify the pipeline:
1.  Check that `data/results/shap_summary.json` contains at least 3 features.
2.  Verify `data/results/null_model_comparison.json` shows the trained model RMSE is lower than the null model.
3.  Ensure `data/validation/exclusion_log.json` exists and lists any excluded rows.
4.  Ensure `data/benchmarks/runtime_log.json` exists and contains `start_time`, `end_time`, and `status`.
5.  Ensure `data/results/permutation_pvalues.json` exists and contains adjusted p-values.

## Troubleshooting
*   **"Dataset not found"**: The `fetch.py` script relies on the `matsci/qmof` dataset name. If this changes, update the `DATASET_NAMES` constant in `code/data/fetch.py`.
*   **"Memory Error"**: Reduce the `SAMPLE_SIZE` in `code/data/fetch.py` or enable streaming.
*   **"Type I Filter Failed"**: Check `data/processed/exclusion_log.json` for the column name issue. The fallback physics-based filter will be used if the column is missing.
