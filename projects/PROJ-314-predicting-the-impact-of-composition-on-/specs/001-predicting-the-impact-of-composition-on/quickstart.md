# Quickstart Guide: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

This guide provides step-by-step instructions to set up the environment, fetch real data, and run the full analysis pipeline for **PROJ-314**.

## 1. Prerequisites & Install

Ensure you have Python 3.11+ installed.

### 1.1. Create Virtual Environment
```bash
cd projects/PROJ-314-predicting-the-impact-of-composition-on-
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
```

### 1.2. Install Dependencies
Install all required packages defined in `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Note: This includes `chemparse`, `scikit-learn`, `shap`, `datasets`, `huggingface_hub`, `pandas`, `numpy`, `scipy`, `pyyaml`, `requests`, `pdfplumber`, `arxiv`, `tabula-py`, `camelot-py`, `psutil`, and `python-dotenv`.*

### 1.3. Environment Configuration
Create a `.env` file in the project root if not already present (copy from `.env.example`):
```bash
cp.env.example.env
```
Ensure any required API keys (e.g., for Materials Project if applicable, though this pipeline primarily uses HuggingFace) are set.

## 2. Data Fetch

This project relies on **real** external data from the HuggingFace dataset repository `materials-science/ceramic-reliability`. The ingestion pipeline is designed to "fail loudly" if this data cannot be fetched; no synthetic fallbacks are permitted.

### 2.1. Verify Data Source
Before running the full pipeline, you can verify the dataset is accessible:
```bash
python code/ingestion.py --validate-dataset
```
This will check connectivity and metadata for `materials-science/ceramic-reliability`.

### 2.2. Ingest Raw Data
The main ingestion script fetches data from HuggingFace and saves raw JSON files to `data/raw/`.
```bash
python code/ingestion.py --fetch-all
```
**Expected Outputs:**
- `data/raw/materials_project_raw.json`
- `data/raw/nist_raw.json`
- `data/raw/arxiv_raw.json` (if arXiv extraction is enabled)
- `data/raw/curated_literature_raw.json`

*If this step fails, check your internet connection and ensure the HuggingFace dataset ID is correct.*

## 3. Running the Pipeline

The full analysis pipeline is orchestrated by `run_pipeline_timing.py`. This script executes data cleaning, descriptor computation, modeling, and reporting in sequence.

### 3.1. Execute Full Pipeline
```bash
python code/run_pipeline_timing.py
```

**What this script does:**
1. **Ingestion & Cleaning**: Loads raw data, filters by sample count (N >= 30), handles range values, and imputes missing descriptors.
2. **Descriptor Computation**: Calculates features like `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`, and `cation_size_variance`.
3. **Data Gap Check**: If valid entries < 30, it generates `data/reports/data_availability_report.json` and halts.
4. **Modeling**: Trains Random Forest and Gradient Boosting models with 5-fold stratified cross-validation.
5. **Evaluation**: Computes MAE, R², and performs permutation testing for statistical significance.
6. **Interpretability**: Generates SHAP values, calculates VIF, and ranks feature importance.
7. **Reporting**: Aggregates all results into final JSON and PNG artifacts.

### 3.2. Expected Execution Time
Depending on the dataset size and hardware, this may take several minutes. The pipeline includes a timeout wrapper to prevent indefinite hangs.

## 4. Verifying Outputs

Upon successful completion (exit code 0), the following artifacts **must** exist in the `data/` directory:

### 4.1. Processed Data
- `data/processed/step_final_cleaned.csv`: The final dataset used for modeling.

### 4.2. Reports & Metrics
- `data/reports/data_availability_report.json`: (Generated if data is insufficient, otherwise standard metrics).
- `data/results/model_metrics.json`: MAE, R², and stratification reports.
- `data/results/baseline_metrics.json`: Performance of the global mean baseline.
- `data/results/leakage_report.json`: Analysis of feature leakage.
- `data/results/stability_metrics.json`: Cross-validation stability scores.
- `data/results/feature_ranking_table.csv`: Ranked list of feature importances.
- `data/results/permutation_test_report.json`: Statistical significance results.

### 4.3. Models & Artifacts
- `data/models/best_model.pkl`: The trained model (if statistically significant).
- `data/artifacts/shap_summary.png`: Visual summary of SHAP values.
- `data/artifacts/feature_importance_plot.png`: Bar chart of top features.

### 4.4. Verification Command
To programmatically verify that all expected files were created:
```bash
python code/verify_citation_log.py # Checks logs
# Or manually check:
ls -l data/reports/data_availability_report.json
ls -l data/results/baseline_metrics.json
ls -l data/results/feature_ranking_table.csv
ls -l data/results/leakage_report.json
ls -l data/results/shap_summary.png
ls -l data/results/stability_metrics.json
```

If any of these files are missing, the pipeline did not complete successfully. Review `logs/pipeline.log` for error details.

## Troubleshooting

- **ImportError: cannot import name 'Composition' from 'chemparse'**: Ensure `chemparse` is installed correctly. The pipeline uses `parse_formula` from `chemparse`.
- **HuggingFace Connection Failed**: Check network settings or try `huggingface-cli login` if authentication is required.
- **Memory Error**: The pipeline monitors memory usage. If it exceeds the limit (default 6GB), it will raise a `MemoryError`. Reduce the dataset sample size or increase system RAM.
- **Data Gap**: If the dataset contains fewer than 30 valid entries after filtering, the pipeline will halt and generate a data availability report. This is expected behavior per the project's safety constraints.