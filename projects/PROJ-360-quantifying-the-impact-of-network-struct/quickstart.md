# Quickstart Guide: Quantifying the Impact of Network Structure on Heat Diffusion

This guide details how to run the full pipeline for project **PROJ-360**.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`
- Set the `MP_API_KEY` environment variable:
 ```bash
 export MP_API_KEY="your_materials_project_api_key_here"
 ```

## Full Pipeline Execution

Run the following commands in sequence. Each command corresponds to a specific task in `tasks.md`.

### 1. Setup & Download
```bash
python code/download.py --limit 50 --output data/raw/cif/
python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/
```

### 2. Compute Metrics & Analyze
```bash
python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv
python code/analyze.py --input data/processed/metrics.csv --output data/processed/filtered_features.csv
```

### 3. Train Model & Validate
```bash
python code/train_model.py --input data/processed/filtered_features.csv --output models/thermal_predictor.pkl
python code/stratified_cv.py --model models/thermal_predictor.pkl --input data/processed/filtered_features.csv --output results/model_performance.json
```

### 4. Robustness & Reporting
```bash
python code/robustness_check.py --input data/processed/filtered_features.csv --output results/robustness_check.json
python code/generate_residuals.py --model models/thermal_predictor.pkl --input data/processed/filtered_features.csv --output results/model_residuals.png
python code/report.py --performance results/model_performance.json --output results/final_report.md
```

### 5. Verification
```bash
python code/verify_report_limitations.py --report results/final_report.md
python code/validate_artifacts.py --input data/processed/filtered_features.csv --output results/validations.json
```

## Verifying the "Limitations" Section

To verify that the mandatory "Limitations" text is present in the final report:

1. Open `results/final_report.md`.
2. Ensure the following text appears exactly as written:
 > "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects."

Alternatively, run the verification script:
```bash
python code/verify_report_limitations.py --report results/final_report.md
```
This script will exit with code 0 if the text is found, or 1 if it is missing.

## Troubleshooting

- **Missing API Key**: Ensure `MP_API_KEY` is set in your environment.
- **No CIF files**: If `data/raw/cif/` is empty, re-run `download.py` with a valid API key.
- **Model not found**: Ensure `train_model.py` has been executed before running `stratified_cv.py` or `generate_residuals.py`.
- **Missing filtered features**: Ensure `analyze.py` has been executed to produce `data/processed/filtered_features.csv`.