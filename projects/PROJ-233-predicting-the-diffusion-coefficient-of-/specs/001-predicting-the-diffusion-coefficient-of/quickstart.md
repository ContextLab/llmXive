# Quickstart: Running the Hydrogen Diffusion Prediction Pipeline

These instructions assume a fresh GitHub Actions runner (or a local Linux environment with Python 3.11).

## 1. Clone the repository & install dependencies
```bash
git clone https://github.com/your-org/PROJ-233-hydrogen-diffusion.git
cd PROJ-233-hydrogen-diffusion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2. Verify data availability
```bash
python -c "from src.pipeline.ingest import check_dataset; check_dataset()"
```
- If the verified NIST dataset is unavailable (the usual case), the script will log a warning and generate a synthetic dataset (`data/raw/synthetic_diffusion.parquet`).

## 3. Run the full pipeline
```bash
python -m src.cli.run_pipeline \
    --seed 42 \
    --ram_limit_gb 6 \
    --time_limit_h 6 \
    --bootstrap_iters 1000 \
    --bayes_time_h 2
```
- The script orchestrates all phases (Ingestion → Bootstrap → Power Analysis).  
- Logs are written to `logs/run_$(date +%Y%m%d_%H%M%S).log`.  
- If RAM or wall‑clock limits are approached, the fallback to a reduced‑size sample subset is triggered automatically (see Phase 6).

## 4. Inspect results
```bash
# Performance table
python -c "import pandas as pd; print(pd.read_parquet('data/results/model_performance.parquet'))"

# Interaction table
python -c "import pandas as pd; print(pd.read_parquet('data/results/interaction_terms.parquet'))"

# Bootstrap CI summary
python -c "import pandas as pd; print(pd.read_parquet('data/results/bootstrap_ci.parquet'))"

# External validation summary (checks >70% variance claim)
python -c "import pandas as pd; print(pd.read_parquet('data/results/external_validation.parquet'))"

# Power analysis results
python -c "import pandas as pd; print(pd.read_parquet('data/results/power_analysis.parquet'))"
```

## 5. View generated figures
```bash
open figures/rmse_comparison.png
open figures/shap_interaction_heatmap.png
open figures/bootstrap_feature_importance_violin.png
open figures/external_validation_plot.png
open figures/power_analysis_plot.png
```

## 6. Contract validation (optional)
```bash
pytest -q tests/contract
```
All output files are validated against the schemas in `contracts/`. The test suite will fail if any required column is missing or if data types do not match.

## 7. Re‑run with a real dataset (when available)
Replace `data/raw/synthetic_diffusion.parquet` with a file that matches the schema defined in `contracts/dataset.schema.yaml` and re‑execute step 3. The pipeline will automatically detect the new file and skip synthetic generation.

---

