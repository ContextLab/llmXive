# Quickstart: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

## Prerequisites
- Python 3.11 or newer  
- `git` and internet access (to download datasets)  
- Virtual environment tool (`venv` or `conda`)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-531-the-impact-of-visual-motion-on-perceived

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

The pipeline is orchestrated by a single Bash wrapper that respects task dependencies:

```bash
bash run_pipeline.sh
```

The script performs the following **ordered** steps (reflecting the corrected task flow):

1. **Data Acquisition** (`code/download_data.py`) – attempts to download each verified URL, checks for required variables, validates instrument DOI, citation count **and** Cronbach's α ≥ 0.70 (FR‑013). Writes `data/raw/download_status.json`.  
2. **Synthetic Generation** (`code/generate_synthetic.py`) – runs automatically only if `download_status.use_synthetic` is true (i.e., real download failed or variables missing). Creates `data/raw/synthetic_data.csv` with a known β structure and independent trigger.  
3. **Pre‑processing** (`code/preprocess.py`) – extracts latency, smoothness, derives lead time (with Pearson < 0.05, partial < 0.05, permutation p > 0.10 checks), aggregates agency items, computes Cronbach's α (require α ≥ 0.70), validates instrument via DOI/citations **and** α, drops rows with missing motion or agency fields (≥ 5 % loss tolerated).  
4. **Power Analysis** (`code/power_analysis.py`) – calculates detectable effect size for the **effective** sample size after missingness removal and for up to three covariates; records `effective_n`, `detectable_f2`, `power`, `sc001_pass`, and `power_pass` in `modeling_config.json`.  
5. **Gate Enforcement** (`code/enforce_gates.py`) – reads `sc001_pass` and `vif_pass`; logs warnings if any gate fails but **does not abort**; downstream tasks may still run and final reports will note any failures.  
6. **Output Cleaned CSV** (`code/output_cleaned_csv.py`) – writes the final `analysis_ready.csv` after all gates, including a `status` column summarising gate outcomes.  
7. **Model Fitting** (`code/model_fitting.py`) – fits OLS, Ridge, and Random Forest (including optional covariates `age`, `vr_experience`, `task_difficulty`).  
8. **Multiple‑Comparison Correction** (`code/significance_correction.py`) – applies Bonferroni (≤5 tests) or Benjamini‑Hochberg (>5 tests) **to both OLS and Ridge**; records the method in `metadata.correction_method`.  
9. **Cross‑Validation** (`code/cross_validation.py`) – 5‑fold CV, stores R² & RMSE per fold in `model_metrics.json`.  
10. **Sensitivity Analysis** (`code/sensitivity_analysis.py`) – coefficient‑threshold sweep with runtime guard; outputs `sensitivity_report.json`.  
11. **Visualization** (`code/visualization.py`) – creates scatter plots, importance bar chart, PDP; saves PNGs under `data/processed/figures/`.  
12. **Interpretability Review** (`code/reviewer_simulation.py`) – simulates five reviewer scores; aborts if average < 4.0 (SC‑005).  
13. **Final Artifact Generation** – `model_metrics.json` (validated against `contracts/analysis_output.schema.yaml`) and `visualization_report.json` (average reviewer rating) are written; their SHA‑256 hashes are recorded in `state/projects/PROJ-531-the-impact-of-visual-motion-on-perceived.yaml`.

All intermediate artifacts are logged in `data/processed/` with checksums recorded automatically.

## Verifying Success Criteria

| Success Criterion | Artifact | How to Verify |
|-------------------|----------|---------------|
| SC‑001 (≥ 100 complete observations) | `modeling_config.json` → `sc001_pass` | `cat data/processed/modeling_config.json \| jq .sc001_pass` |
| SC‑002 (5‑fold CV metrics) | `model_metrics.json` → `cross_validation_metrics` | Contains `r2_mean`, `r2_std`, `rmse_mean`. |
| SC‑003 (Multiple‑comparison control) | `model_metrics.json` → `statistical_significance` (corrected) | Verify corrected p‑values ≤ 0.05 only after Bonferroni/BH. |
| SC‑004 (VIF < 5) | `vif_report.json` → `vif_pass` | `true`. |
| SC‑005 (Visualization clarity) | `visualization_report.json` → `average_rating` | Must be ≥ 4.0. |
| FR‑013 (Instrument validity) | `download_status.json` → `instrument_valid` | `true` for real data; synthetic instrument always true. |
| FR‑014 (Power analysis) | `modeling_config.json` → `power_pass` | `true`. |

If any check fails, the pipeline logs a clear warning; the user can adjust parameters (e.g., increase synthetic N) and re‑run.

## Troubleshooting

- **“Insufficient sample size”** – Check `modeling_config.json` for `sc001_pass`. If `false`, consider increasing synthetic N or locating a larger real dataset.  
- **“Collinearity detected (VIF ≥ 5)”** – The OLS model will drop offending predictors; review `vif_report.json` for details.  
- **“Instrument invalid”** – The DOI lookup failed or citation count < 10 **or** Cronbach's α < 0.70; the pipeline will fall back to synthetic data.  
- **“Visualization rating below threshold”** – Adjust `visualization.py` parameters (e.g., increase figure DPI, add axis labels) and re‑run.  

All logs are stored under `logs/` for reproducibility.
