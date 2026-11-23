# Quickstart Guide: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

This guide provides step-by-step instructions to set up the environment, fetch real data, and execute the full analysis pipeline for predicting Weibull modulus from ceramic composition.

## 1. Prerequisites & Install

### System Requirements
- Python 3.11 or higher
- pip package manager
- 8GB+ RAM recommended for full dataset processing

### Environment Setup
1. Navigate to the project root:
 ```bash
 cd projects/PROJ-314-predicting-the-impact-of-composition-on-
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

 *Required packages include: pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy, datasets, huggingface_hub, arxiv, pdfplumber, psutil, python-dotenv, pydantic.*

4. (Optional) Configure environment variables:
 ```bash
 cp.env.example.env
 # Edit.env to add API keys if required by specific data sources
 ```

## 2. Data Fetch

The pipeline fetches real ceramic reliability data from the HuggingFace dataset repository `materials-science/ceramic-reliability`.

**Verification Step**: Before running the full pipeline, verify the dataset is accessible:
```bash
python code/verify_hf_dataset.py
```
*This script checks connectivity and metadata existence for the target dataset.*

**Primary Data Sources**:
- **HuggingFace**: `materials-science/ceramic-reliability` (Aggregates MP, NIST, and literature data)
- **ArXiv**: Supplementary data extracted via `arxiv` search and `pdfplumber`/`tabula-py` extraction.

*Note: The pipeline is configured to FAIL LOUDLY if data cannot be fetched. Do not attempt to run with synthetic fallbacks.*

## 3. Running the Pipeline

Execute the full end-to-end analysis pipeline using the timing wrapper:

```bash
python code/run_pipeline_timing.py
```

**What this command does**:
1. **Setup Directories**: Ensures `data/raw/`, `data/processed/`, `data/results/`, `data/reports/`, and `data/artifacts/` exist.
2. **Data Ingestion**: Fetches and cleans data from HuggingFace and ArXiv sources.
3. **Descriptor Computation**: Calculates physical descriptors (atomic radius, electronegativity, VEC, etc.).
4. **Modeling**: Trains Random Forest and Gradient Boosting models with stratified cross-validation.
5. **Evaluation**: Performs baseline comparison, permutation testing, and leakage checks.
6. **Interpretation**: Generates SHAP values, feature rankings, and stability metrics.
7. **Reporting**: Compiles final metrics and compliance reports.

**Expected Duration**: 10-30 minutes depending on dataset size and system resources.
**Memory Limit**: The pipeline monitors memory usage and will halt if usage exceeds 6GB (configurable via `MEMORY_LIMIT_GB` in `.env`).

## 4. Verifying Outputs

Upon successful completion (exit code 0), verify the following artifacts exist in the `data/` directory:

### Core Reports
- `data/reports/data_availability_report.json`: Confirms data sufficiency (N >= 30).
- `data/reports/final_report.json`: Comprehensive summary of model performance and findings.

### Model Results
- `data/results/baseline_metrics.json`: Performance of the global mean baseline.
- `data/results/model_metrics.json`: MAE, R², and stratification reports for trained models.
- `data/results/leakage_report.json`: Results of the feature leakage check.
- `data/results/permutation_test_report.json`: Statistical significance validation.
- `data/results/cv_split_report.json`: Stratification distribution metrics.

### Interpretability Artifacts
- `data/results/feature_ranking_table.csv`: Ranked list of feature importances.
- `data/results/stability_metrics.json`: Cross-validation stability scores (CV of top 5 features).
- `data/results/fold_importances.json`: Feature importance per CV fold.
- `data/artifacts/shap_summary.png`: SHAP summary plot visualization.

### Raw & Processed Data
- `data/raw/materials_project_raw.json`: Raw fetch from HuggingFace.
- `data/processed/step_final_cleaned.csv`: Cleaned dataset ready for modeling.

If any of these files are missing or the pipeline exits with a non-zero code, check `logs/pipeline.log` for detailed error traces.

## Troubleshooting

- **ImportError: cannot import name 'Composition'**: Ensure `chemparse` is updated to the version specified in `requirements.txt`.
- **MemoryError**: Reduce `MEMORY_LIMIT_GB` in `.env` or process data in chunks (if supported).
- **Data Fetch Failed**: Check internet connection and verify the HuggingFace dataset ID `materials-science/ceramic-reliability` is correct.
- **Insufficient Data**: If the pipeline halts with "Power Limitation: Insufficient data", the `data/reports/data_availability_report.json` will contain the specific count.