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

**Note**: The raw **temperature** column is **kept** as a predictor for the XGBoost and Random Forest models (as required by FR‑008), while the linear baseline will use only the reciprocal temperature (`inv_temperature`). This respects the collinearity handling described in the plan.

## 3. Run the full pipeline

```bash
python -m src.cli.run_pipeline \
    --seed 42 \
    --ram_limit_gb 6 \
    --time_limit_h 6 \
    --bootstrap_iters 1000 \
    --bayes_time_h 2
```

The pipeline orchestrates ingestion (including raw temperature as a predictor for the non‑linear models and the reciprocal temperature for all models), nested cross‑validation with Bayesian optimization, model evaluation, SHAP interaction analysis, bootstrap robustness checks, and power analysis. Results are written to `data/results/` and figures to `figures/`.

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

Unit tests use the small hard‑coded fixture in `tests/data/fixture_rows.csv`
(never used for results); contract tests validate all output schemas.
