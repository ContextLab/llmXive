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
# Real data: verified TIDE CSV
python -m src.data.acquire_real   # downloads, verifies SHA‑256, maps to binary ground_truth_label

# Synthetic edge‑cases (deterministic)
python -m src.data.generate_synthetic   # creates .py files under data/synthetic/
```

## 4. Extract structural features
```bash
python -m src.features.extract   # reads all .py files, estimates depth/scope, writes data/features.csv (includes sha256)
```

## 5. Run the two detection pipelines
```bash
# Static heuristic (CPU‑only, deterministic)
python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv

# Generative LLM (Native CPU distilgpt2, deterministic decoding)
python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv
```

## 6. Consolidate results and create train/validation splits
```bash
python -m src.pipelines.consolidate   # creates data/merged_results.csv (SSoT)
python -m src.data.split_data          # writes train/validation index files (seed=42)
```

## 7. Perform statistical analyses
```bash
python -m src.analysis.logistic        # logistic regression, EPV check, PDP threshold + bootstrap CI
python -m src.analysis.mcnemar         # stratified McNemar tests + Holm‑Bonferroni
python -m src.analysis.sensitivity     # probability‑cutoff sweep & variance reporting
python -m src.analysis.efficiency      # total runtime & CPU utilisation check
```

## 8. Generate figures and final tables
```bash
python -m src.analysis.visualize   # writes PNGs under outputs/
```

## 9. Validate contracts
```bash
pytest -q tests/contract
```
All tests must pass; they confirm that `data/merged_results.csv` conforms to `contracts/detection_results.schema.yaml`.

If everything succeeds, you will have:
- `outputs/` containing the ROC curve, PDP threshold plots, and McNemar significance plot.  
- `data/analysis_summary.json` containing the consolidated statistical results.

The entire pipeline completes within the CI limits (≈ 4 h CPU time, ≤ 7 GB RAM). No GPU is required.

## 10. Clean up (optional)
```bash
deactivate
rm -rf .venv data/__pycache__ src/__pycache__
```
