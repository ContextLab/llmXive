# Quickstart: Semantic Collapse Threshold Study

This guide walks you through reproducing the full end‑to‑end pipeline on a fresh GitHub Actions runner.

## Prerequisites
- Python 3.11 (installed automatically by the CI environment)  
- No manual GPU provisioning needed; the pipeline will auto‑offload to a free Kaggle GPU if required.

## Step‑by‑Step

1. **Clone the repository** (already present in the CI workspace).

2. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the pipeline orchestrator**
   ```bash
   python -m src.cli.main \
       --stage all \
       --sample-size 50000 \
       --seed 2026 \
       --log-dir logs/
   ```
   - `--stage all` executes every phase in order (download → distort → sss → collapse → regression → analysis).  
   - The script automatically checks for GPU availability; if unavailable, it falls back to a CPU‑only reduced sample (of modest size) and logs the change.

4. **Outputs**
   - `data/derived/subset.parquet` – stratified 50 k clip list.  
   - `data/derived/stress_curves.parquet` – Several distortion rows per clip, ASR hypotheses, WER, SSS.  
   - `data/derived/collapse_points.parquet` – deterministic classification labels + detection parameters (Schema 2).  
   - `data/derived/collapse_point.parquet` – inflection‑point intensity records (primary regression target, Schema 3).  
   - `data/derived/critical_vector.parquet` – interaction coefficients and SHAP strengths per ASR model (Schema 4).  
   - `data/derived/model_metrics.parquet` – R², MAE, permutation baseline ΔR², sensitivity CVs.  
   - `reports/figures/` – PDF/PNG figures for the paper (stress curves, interaction heatmaps, SHAP summary).  

5. **Verification**
   ```bash
   pytest -q tests/
   python -m src.tests.contract.test_contracts
   ```
   - Unit tests confirm each stage’s contract compliance.  
   - Contract tests validate that the parquet files conform to the schemas defined in `contracts/`.

6. **Inspect Results**
   ```python
   import pandas as pd
   metrics = pd.read_parquet("data/derived/model_metrics.parquet")
   print(metrics)
   ```
   Verify that `R2 >= 0.6`, `perm_drop >= 0.20`, and `coeff_cv <= 0.10`.  

7. **Re‑run with alternative parameters (optional)**
   ```bash
   python -m src.cli.main \
       --stage regression \
       --sss-threshold-factor 0.6 \
       --wer-multiplier 2.5
   ```
   This triggers the sensitivity analysis (FR‑006).

## FAQ
- **Do I need a GPU?** No. The pipeline will attempt GPU for the distortion stage; if it fails, it will automatically down‑sample and continue on CPU, logging the change.
- **Where are the raw datasets stored?** Under `data/raw/` after download; checksums are recorded in the project state file.
- **How is reproducibility ensured?** All random seeds are fixed (`seed=2026`), and every transformation writes a new file with a SHA‑256 hash recorded in the state file.
- **Which contract files are generated?** `collapse_point.parquet` follows `contracts/collapse_point.schema.yaml`; `critical_vector.parquet` follows `contracts/critical_vector.schema.yaml`.

Enjoy your reproducible semantic collapse analysis!  
