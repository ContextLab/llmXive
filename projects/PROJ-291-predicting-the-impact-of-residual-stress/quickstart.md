# Quickstart: Predicting Residual‑Stress Impact on Fatigue Life

> Assumes a recent Python 3.11 interpreter and internet access from the repository root.

## 1. Set up the environment
```bash
# Create a clean virtual environment
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Verify the runner environment (CI sanity check)
```bash
# Checks that all required scientific packages can be imported and that
# the bundled raw data files have the correct checksums.
python -m code.src.env_check
```

## 3. Run the full analysis pipeline (end‑to‑end)
```bash
# One‑command end‑to‑end execution:
python -m code.src.run_e2e
```

The pipeline will:
1. Ingest the bundled raw CSVs, compute checksums, standardise units, and write `data/processed/unified_fatigue.csv`.
2. Compute the proxy‑measured agreement and write `data/results/proxy_agreement.csv`.
3. Record phase runtimes in `data/results/runtime_summary.csv` and write a summary JSON `data/results/e2e_summary.json`.

## 4. Inspect results
- Unified dataset: `data/processed/unified_fatigue.csv`
- Proxy‑agreement metrics: `data/results/proxy_agreement.csv`
- Runtime summary: `data/results/runtime_summary.csv`
- End‑to‑end summary: `data/results/e2e_summary.json`

## 5. Run automated tests
```bash
pytest -q
```

All steps are designed to complete within the GitHub Actions free‑tier limits
(≤ 6 h runtime, < 7 GB RAM). The synthetic data is **not** used for external
scientific conclusions and is **never used for mediation**; it only validates
that the pipeline runs without error.
