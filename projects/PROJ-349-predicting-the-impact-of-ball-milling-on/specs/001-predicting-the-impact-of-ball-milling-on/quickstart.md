# Quickstart: Predicting Ball‑Milling PSD

This guide walks a new developer through setting up the environment, running the full pipeline, and reproducing the key results on a fresh GitHub Actions runner.

## 1. Clone the Repository & Set Up Environment
```bash
git clone
cd PROJ-349-predicting-the-impact-of-ball-milling-on
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the End‑to‑End Pipeline
```bash
# Step 0 – Clean previous artefacts
rm -rf data/processed/* results/* logs/*

# Step 1 – Ingest raw data
python -m src.ingest.materials_project
python -m src.ingest.nist_repo
python -m src.ingest.arxiv_extractor

# Step 2 – Preprocess & validate
python -m src.preprocess.pipeline

# Step 3 – Train models (fallback handled automatically)
python -m src.model.train_gpr # may be skipped automatically
python -m src.model.train_rf

# Step 4 – Baseline & evaluation
python -m src.model.baseline_lr
python -m src.evaluate.metrics
python -m src.evaluate.statistical_tests

# Step 5 – Interpretability
python -m src.interpret.partial_dependence
python -m src.interpret.feature_importance

# Step 6 – Assemble report artefacts
python -m src.utils.generate_report # creates results/summary.txt and figures
```

All scripts log progress to `logs/` and write artefacts under `data/processed/`, `models/`, and `results/`.

## 3. Verify Contract Compliance
```bash
pytest -q tests/contract/test_dataset_schema.py
```
A passing test confirms that the final dataset conforms to `contracts/dataset.schema.yaml`.

## 4. Run on GitHub Actions (CI)
The repository includes `.github/workflows/ci.yml`. To trigger a CI run locally:
```bash
act -j full-pipeline # requires the `act` CLI (optional)
```
The CI job enforces the 6‑hour wall‑clock limit and the 5 GB RAM ceiling; any breach causes an automatic failure.

## 5. Expected Outputs
- `data/processed/ball_milling_dataset.parquet` – validated dataset.
- `models/gpr.pkl` (if trained) and `models/rf.pkl`.
- `results/metrics.csv` – R², RMSE, MAE for each model.
- `results/t_test_summary.txt` – p‑values, Bonferroni‑adjusted α, statistical power.
- `results/partial_dependence_*.png` – ≤ 10 MB total (SC‑005).
- `results/feature_importance.json` – ranked RF importance scores.

## 6. Reproducibility Checklist
- Random seeds are fixed in `src/utils/seed.py`.
- All external data fetched via the same URLs/APIs each run.
- Checksums for raw and processed files are recorded in `state/projects/...yaml`.

You can now explore the results, adjust hyper‑parameters, or extend the analysis while staying within the project's constitutional constraints.

---
