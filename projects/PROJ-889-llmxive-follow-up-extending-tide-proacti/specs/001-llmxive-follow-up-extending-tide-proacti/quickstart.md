# Quickstart: Extending TIDE for Boundary Analysis

These instructions let you reproduce the entire study on a fresh GitHub Actions runner (or locally on a Linux machine with Python 3.11).

## 1. Clone the repository & navigate
```bash
git clone 
cd llmxive-followup-tide
```

## 2. Create a clean virtual environment and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Download the real dataset and generate synthetic data
```bash
# Real data: CodeXGLUE defect‑detection (open, no URL needed)
python -m src.data.acquire   # pulls dataset, runs manual mapping to hidden‑problem labels, verifies checksum
# Synthetic edge‑cases
python -m src.data.generate_synthetic   # creates a set of synthetic .py files under data/synthetic/
```

## 4. Extract structural features
```bash
python -m src.features.extract   # reads all .py files, writes data/features.csv (includes `origin`)
```

## 5. Run the two detection pipelines (producing enriched result files)
```bash
# Static heuristic (CPU‑only, deterministic)
python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv (full schema)

# Generative LLM (quantized GPT‑2, CPU‑only)
python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv (full schema)
```

## 6. Consolidate results and split data
```bash
python -m src.pipelines.consolidate   # creates data/merged_results.csv (full schema, SSoT)
python -m src.analysis.split_data      # creates train/validation splits (seed=42)
```

## 7. Perform statistical analyses
```bash
python -m src.analysis.logistic        # logistic regression + marginal threshold + bootstrap CI
python -m src.analysis.mcnemar         # stratified McNemar tests + Holm‑Bonferroni
python -m src.analysis.sensitivity     # probability‑cutoff sweep & variance reporting
python -m src.analysis.efficiency      # total runtime & CPU usage report
```

## 8. Generate figures and final tables
```bash
python -m src.analysis.visualize   # writes PNGs under outputs/
```

## 9. Validate contracts
```bash
pytest -q tests/contract
```

If all tests pass, the study has reproduced the required artifacts:
- `outputs/` contains the ROC curve, marginal‑threshold heatmaps, and McNemar significance plot.
- JSON/CSV summary files are ready for the paper pipeline.

All steps run within the CI limits (≈ 4 h total CPU time, ≤ 7 GB RAM). No GPU is required.

## 10. Clean up (optional)
```bash
deactivate
rm -rf .venv data/__pycache__ src/__pycache__
```

---


