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

Place a real measurements file at `data/raw/diffusion_measurements.csv` matching
`contracts/dataset.schema.yaml` (columns: `sample_id`, `composition`,
`processing_params`, `temperature`, `diffusion_coefficient`; diffusion
coefficients in any documented unit — harmonized to m²/s by the pipeline).

**Note**: no verified open download for hydrogen‑diffusion data currently
exists (see research.md). If the file is absent, the pipeline exits non‑zero
with an explicit data‑availability message rather than fabricating data.

## 3. Run the full pipeline

```bash
python -m src.cli.run_pipeline \
    --seed 42 \
    --ram_limit_gb 6 \
    --time_limit_h 6 \
    --bootstrap_iters 1000 \
    --bayes_time_h 2
```

Orchestrates ingestion → nested training → baseline comparison → SHAP
interactions → external hold‑out → bootstrap → power analysis. Logs go to
`logs/`. RAM/wall‑clock guards trigger the documented fallbacks (FR‑006).

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
