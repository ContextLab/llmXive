# Quickstart Guide: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

This guide provides step-by-step instructions to set up the environment, fetch real data, and execute the full machine learning pipeline for predicting Weibull modulus based on ceramic composition.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git
- Access to the Materials Project API (API key required)

## 1. Project Setup

### 1.1 Clone and Navigate
```bash
git clone <repository-url>
cd projects/PROJ-314-predicting-the-impact-of-composition-on-
```

### 1.2 Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.4 Configure Environment Variables
Create a `.env` file in the project root based on the template:
```bash
cp.env.example.env
```

Edit `.env` to add your API keys:
```ini
MP_API_KEY=your_materials_project_api_key
NIST_API_KEY=your_nist_api_key # If applicable
DATA_SOURCE_URL=
```

## 2. Data Fetching

The pipeline requires real ceramic property data from external sources. The ingestion module will fetch data from:
1. **Materials Project**: For stoichiometry and crystal structure data.
2. **NIST**: For mechanical property data (Weibull modulus).
3. **arXiv**: For supplementary literature data (if configured).

**Note**: Ensure your `.env` file contains valid API keys before proceeding.

## 3. Pipeline Execution

The full pipeline consists of three main stages: Ingestion, Modeling, and Interpretation.

### 3.1 Run the Full Pipeline
Execute the main pipeline script:
```bash
python code/run_pipeline_timing.py
```

This script will:
1. **Ingest Data**: Fetch raw data, clean it, and compute elemental descriptors.
 - Output: `data/processed/cleaned_dataset.csv`
 - If data is insufficient (< 30 valid entries), the process halts and generates a report at `data/reports/data_availability_report.json`.
2. **Train Models**: Train Random Forest and Gradient Boosting models with cross-validation.
 - Output: `data/results/model_metrics.json`, `data/models/best_model.pkl`
3. **Interpret Results**: Generate SHAP values, VIF diagnostics, and final reports.
 - Output: `data/results/shap_summary.png`, `data/results/feature_ranking_table.csv`, `data/results/final_report.json`

### 3.2 Monitor Runtime
The pipeline execution time is logged to `data/results/runtime_metrics.json`.
Ensure the total duration is under 6 hours (SC-005).

## 4. Verification & Validation

### 4.1 Validate Quickstart Guide
Run the validation script to ensure all paths and commands in this guide are correct:
```bash
bash scripts/validate_quickstart.sh
```
Success is indicated by exit code 0 and no errors in `logs/validation.log`.

### 4.2 Check Data Gap Protocol
If the pipeline halts due to insufficient data, review `data/reports/data_availability_report.json` for details.

### 4.3 Review Reports
- **Model Metrics**: `data/results/model_metrics.json` (MAE, R², significance)
- **Leakage Report**: `data/results/leakage_report.json`
- **Final Report**: `data/results/final_report.json` (includes confidence intervals)

## 5. Troubleshooting

- **Missing API Keys**: Ensure `MP_API_KEY` is set in `.env`.
- **Data Fetch Failures**: Check network connectivity and API rate limits. The pipeline will fail loudly if real data cannot be fetched (no synthetic fallback).
- **Insufficient Data**: If `N < 30`, the pipeline halts. Check `data/reports/data_availability_report.json` for the reason code.
- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.

## 6. Next Steps

- **Extend Data Sources**: Implement additional fetchers in `code/ingestion.py`.
- **Model Tuning**: Adjust hyperparameters in `code/modeling.py`.
- **Feature Engineering**: Add new descriptors in `code/descriptors.py`.

For detailed API documentation, refer to the `docs/` directory.