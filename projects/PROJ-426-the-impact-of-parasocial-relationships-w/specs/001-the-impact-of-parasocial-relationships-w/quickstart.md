# Quickstart: The Impact of Parasocial Relationships with AI Companions on Loneliness

These instructions let you reproduce the full analysis on a fresh GitHub Actions runner or local machine.

## 1. Clone the Repository & Set Up Environment
```bash
git clone
cd parasocial-loneliness
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Data Checksums (optional but recommended)
```bash
python src/utils/checksums.py verify
```
If any checksum fails, the pipeline will re‑download the raw files.

## 3. Run the End‑to‑End Pipeline
```bash
# Phase 1 – Ingest raw data (includes schema validation)
python src/ingest/download_loneliness.py # pulls Zenodo dataset (halts if schema invalid)
python src/ingest/fetch_pushshift.py # pulls AI‑companion logs

# Phase 2 – Match users
python src/match/user_match.py

# Phase 3 – Feature engineering
python src/features/usage_metrics.py
python src/features/attachment_proxy.py

# Phase 4 – Modeling
python src/modeling/mixed_effects.py
python src/modeling/bootstrap_ci.py

# Phase 5 – Subgroup analysis (age ≥ 60)
python src/modeling/mixed_effects.py --subgroup age_ge_60

# Phase 6 – Generate report
python src/report/generate_report.py
```
Each script logs progress to `logs/` and writes its output to `data/` (raw → intermediate → final) and `results/`. **Note**: If the Zenodo dataset lacks linkable user IDs, `download_loneliness.py` will halt with a "Data Linkage Impossible" error.

## 4. Inspect Results
- `results/mixed_effects_summary.csv` – fixed‑effect estimates, p‑values, bootstrap CIs.
- `results/subgroup_60plus.csv` – same format for the older‑adult subgroup.
- `reports/analysis_report.html` – interactive HTML with tables, plots, and runtime summary.

## 5. Run Tests (optional)
```bash
pytest -v
```
Unit tests cover data download, hashing, and feature calculations; integration tests run the full pipeline on a tiny synthetic subset (≈ 100 users) to ensure end‑to‑end functionality.

## 6. Re‑run with a Different Random Seed (if needed)
All stochastic steps accept `--seed <int>`; default seed is set to a standard value (as required by FR‑006).

---