# Quickstart: Extending TIDE for Boundary Analysis

These steps reproduce the full study on a fresh GitHub Actions runner (or any Linux machine with Python 3.11).

## 1. Clone the repository & navigate
```bash
git clone <REPO_URL>
cd llmxive-followup-tide
```

## 2. Set up a clean virtual environment and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Acquire the real TIDE dataset and generate synthetic edge‑cases
```bash
# Real data: streaming download via HuggingFace datasets (checksum verified)
python -m src.data.acquire_real   # creates data/raw/tide.parquet, verifies SHA‑256, writes data/raw/tide.csv and data/raw/tide.sha256

# Synthetic edge‑cases (deterministic, depth capped at 5, distribution‑matched to real data)
python -m src.data.generate_synthetic --seed 42   # creates .py files under data/synthetic/ and synthetic_manifest.csv
```

## 4. Verify acquisition & generation (optional but recommended)
```bash
pytest -q src/data/test_acquire_real.py   # asserts exit code 0 and checksum match
pytest -q src/data/test_generate_synthetic.py   # asserts manifest has a predetermined number of rows
```

## 5. Extract structural features (preserves `origin`)
```bash
python -m src.features.extract   # reads all .py files, writes data/features.csv (includes origin + sha256)
```

## 6. Run the two detection pipelines
```bash
# Static heuristic (CPU‑only, deterministic)
python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv (includes origin)

# Generative LLM (CPU‑native 8‑bit quantized 7B model `bigcode/starcoderbase-7b`,
# deterministic decoding, run on a sampled subset of a representative set of instances)
python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv (includes origin)
```

## 7. Consolidate results and create train/validation splits
```bash
python -m src.pipelines.consolidate   # creates data/merged_results.csv (long‑format, retains origin)
python -m src.data.split_data          # writes train_ids.txt & val_ids.txt (seed=42)
```

## 8. Perform statistical analyses
```bash
python -m src.analysis.logistic        # logistic regression, EPV check, interaction handling, bootstrap CI
python -m src.analysis.mcnemar         # stratified adaptive McNemar tests + Holm‑Bonferroni
python -m src.analysis.sensitivity     # probability‑cutoff, synthetic‑parameter, binning‑scheme, and covariate inclusion sweeps
python -m src.analysis.efficiency      # total runtime & CPU utilisation check
```

## 9. Generate figures and final tables
```bash
python -m src.analysis.visualize   # writes PNGs under outputs/
```

## 10. Validate contracts
```bash
pytest -q tests/contract
```
All tests must pass; they confirm that `data/merged_results.csv` conforms to `contracts/detection_results.schema.yaml`.

If successful, you will have:
- `outputs/` containing the ROC curve, PDP boundary plots, and McNemar significance bar plot.  
- `analysis/logistic_summary.json` with coefficients, mean AUC, interaction‑aware threshold region (with 95 % CI), and EPV status.  
- `analysis/mcnemar_results.csv` with raw and corrected p‑values for each adaptive bin.  

The entire pipeline completes within the CI limits (≈ 4 h CPU time, ≤ 7 GB RAM). No GPU is required.

## 11. Clean up (optional)
```bash
deactivate
rm -rf .venv data/__pycache__ src/__pycache__
```

---



