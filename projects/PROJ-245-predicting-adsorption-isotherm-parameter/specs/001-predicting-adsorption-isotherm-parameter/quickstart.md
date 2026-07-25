# Quickstart: Predicting Adsorption Isotherm Parameters

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to GitHub Actions (for CI) or local environment

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or venv\Scripts\activate  # Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/requirements.txt
    ```

## Running the Pipeline

### 1. Data Preparation (Synthetic Mode)
Since verified adsorption data is currently unavailable, run the synthetic generator:
```bash
cd projects/PROJ-245-predicting-adsorption-isotherm-parameter/code/
python data/generate_synthetic_data.py --output data/processed/synthetic_adsorption.csv
```

### 2. Training & Evaluation
```bash
python models/train.py --input data/processed/synthetic_adsorption.csv --target langmuir_capacity
```
*Output*: `data/models/best_model.pkl`, `data/benchmarks/metrics.json`.

### 3. SHAP Analysis
```bash
python analysis/shap_analysis.py --model data/models/best_model.pkl --data data/processed/synthetic_adsorption.csv
```
*Output*: `data/figures/shap_summary.png`, `data/reports/feature_importance.json`.

### 4. Generate Final Report
```bash
python analysis/report_gen.py
```
*Output*: `data/reports/final_report.md`.

## Verification

- Check `data/benchmarks/runtime_log.json` for execution status.
- Verify `data/reports/final_report.md` contains FDR-corrected p-values and SHAP plots.
- Ensure `R²` improvement over null model is reported.
