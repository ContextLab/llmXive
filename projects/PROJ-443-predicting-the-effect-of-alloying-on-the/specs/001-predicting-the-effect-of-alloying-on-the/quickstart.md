# Quickstart: Predicting the Effect of Alloying on the Elastic Modulus of High‑Entropy Alloys

## Prerequisites

- Python 3.10+
- API keys for Materials Project and OQMD (if required by specific endpoints).  
- Git repository with this project structure.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-443-predicting-the-effect-of-alloying-on-the
pip install -r code/requirements.txt
```

Create a `.env` file in the repository root:

```text
MATERIALS_PROJECT_API_KEY=your_key_here
OQMD_API_KEY=your_key_here
```

## Running the Full Pipeline

### 1. Verify Citations
```bash
python code/validate_references.py
# Exit code 0 = all citations verified
# Exit code 1 = citation mismatch
# Exit code 2 = unreachable source
```

### 2. Data Ingestion & Feature Engineering
```bash
python code/main.py --stage ingest
```
- Retrieves **exactly** the required number of HEA samples (≥500). If fewer are found, the run aborts and logs a message like  
  `"Retrieved 320 samples; threshold 500 not met"` before exiting.  
- Produces `data/processed/features.csv` (includes ILR features and residual bulk modulus as the target).  
- Mixing enthalpy is **computed only for the Miedema baseline** and **not** used as a predictor.
- **Orthogonality Check**: The pipeline automatically checks for correlation between predictors and Miedema inputs. If high correlation is found, predictors are residualized.

### 3. Model Training
```bash
python code/main.py --stage train
```
- Trains Random Forest, Gradient Boosting, and ElasticNet on **residual bulk modulus** (observed − Miedema).  
- Enforces CPU‑only execution (`n_jobs=1`).  
- Outputs models to `results/models/` and raw metrics to `results/metrics.yaml`.

### 4. Evaluation & Uncertainty
```bash
python code/main.py --stage evaluate
```
- Performs grouped bootstrap with a sufficient number of iterations to ensure robust statistical inference. (or **Bayesian Hierarchical Bootstrap** if <30 groups) to compute 95 % CI for R².  
- Applies Benjamini‑Hochberg FDR correction to model‑performance p‑values.  
- Runs sensitivity analysis sweeping **R² thresholds** {0.25, 0.30, 0.35} and writes variance of false‑positive rates to `results/sensitivity.json`.

### 5. Report Generation
```bash
python code/main.py --stage report
```
- Generates SHAP/Permutation importance, parity plots, partial dependence plots.  
- Inserts the mandatory associational disclaimer: **"Associational Disclaimer: All reported relationships are observational; no causal inference is claimed."**  
- Final summary written to `reports/summary.md`.

## Verification Checklist

- **Sample Count**: `data/source_metadata.yaml` reports ≥ 500 samples.  
- **Group Count**: At least 30 unique element‑set groups; if fewer, `results/metrics.yaml` indicates "Bayesian CI" was used.  
- **Metrics**: `results/metrics.yaml` contains R², RMSE, MAE, 95 % CI (standard or Bayesian), p‑values, and FDR flag.  
- **Sensitivity**: `results/sensitivity.json` lists `thresholds_tested` and `fpr_variance`.  
- **Disclaimer**: Verify the exact disclaimer text in `reports/summary.md`.  

## Troubleshooting

- **Insufficient Samples**: Check the log for the deficit message; consider expanding API query parameters.  
- **Memory Errors**: Ensure no GPU flags are set; reduce bootstrap iterations (not recommended for final run).  
- **Bootstrap Instability**: If `<30` groups, the pipeline will automatically switch to **Bayesian Hierarchical Bootstrap** to compute valid CIs.