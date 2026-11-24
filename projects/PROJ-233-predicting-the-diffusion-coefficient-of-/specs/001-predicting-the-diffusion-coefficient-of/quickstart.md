# Quickstart: Running the Hydrogen Diffusion Prediction Pipeline

Assumes a fresh GitHub Actions runner or local Linux environment with Python 3.11.

## 1. Install dependencies

```bash
# Create a virtual environment in the repository root
python -m venv .venv && source .venv/bin/activate

# Install the pinned dependencies (the file lives at the repository root)
pip install -r requirements.txt
```

## 2. Supply real data (required before any results)

**Option A – Use an open dataset (if one becomes available)**  
If a verified open dataset satisfying the required columns is added to the project configuration (`config/open_dataset_url`), the pipeline will automatically download it. No manual step is needed.

**Option B – Manual entry (current default)**  

1. Locate the CSV template at `data/raw/hydrogen_diffusion_template.csv`.  
2. **Fill** the required columns **`sample_id`, `composition`, `composition_fractions` (optional), `processing_params`, `temperature`, `diffusion_coefficient`**.  
3. For each row, add a **comment** line **above** the row (starting with `#`) that records the source reference (DOI, URL, or full citation). Example:  

   ```csv
   # Source: DOI:10.1016/j.jmst.2022.03.015
   sample_001,["Fe","Cr"],,{"anneal_temp":800,"cool_rate":5},900,1.2e-9
   ```  

4. Save the completed file as `data/raw/diffusion_measurements.csv`. The pipeline will verify the file against `contracts/dataset.schema.yaml`, compute its SHA‑256 checksum (recorded in `data/checksums.sha256`), and abort with an explicit error if the file is missing or malformed.

**Note**: The raw **temperature** column is **kept** as a predictor for XGBoost and Random Forest models (as required by FR‑008), while the linear baseline will use only the reciprocal temperature (`inv_temperature`). This respects the collinearity handling described in the plan.

## 3. Run the full pipeline

```bash
python -m src.cli.run_pipeline \
    --seed 42 \
    --ram_limit_gb 6 \
    --time_limit_h 6 \
    --bootstrap_iters 1000 \
    --bayes_time_h 2
```

Key pipeline steps (performed automatically):

1. **Data acquisition gate** – verifies presence & checksum of `diffusion_measurements.csv`; aborts if < 200 samples.  
2. **Ingestion & descriptor engineering** – computes compositional descriptors, microstructural proxies, and adds `inv_temperature` (used only by the linear baseline).  
3. **Preprocessing** – k‑NN imputation (k=5) on predictor columns only; StandardScaler fitted inside inner CV folds.  
4. **Nested CV** – outer 5‑fold CV with inner Optuna TPE Bayesian optimization (≤ 2 h). Graceful fallback to default grid if time expires.  
5. **Linear baseline** – trained on `inv_temperature` only; RMSE & R² reported.  
6. **Non‑linear models** – XGBoost and Random Forest trained on raw `temperature` (no `inv_temperature`).  
7. **SHAP interaction analysis** – computes mean‑absolute interaction values (descriptive).  
8. **Independent hold‑out evaluation** – uses a [deferred] internal stratified hold‑out (seed = 42) and computes the permutation‑based interaction‑variance share with 95 % bootstrap CI.
9. **Bootstrap robustness** – 1,000 resamples, refitting the full pipeline with fixed hyperparameters; parallelised across 2 CPU cores; produces CIs for top‑5 feature importances and interaction ΔR².  
10. **Power analysis** – a‑priori simulation confirms ≥ 200 samples give ≥ 0.80 power for interaction effect size *f*² ≥ 0.15; post‑hoc analysis reports `f²_interaction`, minimum detectable `f²`, and CI width for the top descriptor.  
11. **Resource guard** – monitors RAM (6 GB limit) and wall‑clock (5 h 55 min); falls back to a 150‑sample reproducible subset if needed.

## 4. Inspect results

```bash
python -c "import pandas as pd; print(pd.read_parquet('data/results/model_performance.parquet'))"
python -c "import pandas as pd; print(pd.read_parquet('data/results/interaction_terms.parquet'))"
python -c "import pandas as pd; print(pd.read_parquet('data/results/bootstrap_ci.parquet'))"
python -c "import pandas as pd; print(pd.read_parquet('data/results/external_validation.parquet'))"
python -c "import pandas as pd; print(pd.read_parquet('data/results/power_analysis.parquet'))"
```

## 5. View figures

`figures/rmse_comparison.png`, `figures/shap_interaction_heatmap.png`,
`figures/bootstrap_feature_importance_violin.png`,
`figures/external_validation_plot.png`, `figures/power_analysis_plot.png`.

## 6. Run tests (no real data required — uses fixture rows)

```bash
pytest -q tests/
```

Unit tests use the small hard‑coded fixture in `tests/data/fixture_rows.csv` (never used for results); contract tests validate all output schemas.
