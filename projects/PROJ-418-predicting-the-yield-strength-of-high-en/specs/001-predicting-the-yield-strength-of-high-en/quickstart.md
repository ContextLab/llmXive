# Quickstart: Predicting HEA Yield Strength

These instructions assume you are running on a fresh GitHub Actions runner or a local Linux environment with **Python 3.11** and **git** installed.

## 1. Clone the repository
```bash
git clone
cd heas-yield-predictor
```

## 2. Set up the Python environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Provide the curated dataset
Place the curated CSV (matching `contracts/dataset.schema.yaml`) at:

```
data/raw/heas_raw.csv
```

If you do not have the file, the pipeline will abort with a clear error (FR‑009).

## 4. Run the full pipeline
```bash
python -m src.cli run \
 --data data/raw/heas_raw.csv \
 --elemental data/elemental_properties.csv \
 --output-dir outputs/
```

The command performs:
1. Validation of inputs (FR‑013, FR‑009).
2. Descriptor computation (FR‑002).
3. Train‑test split, Random Forest training (FR‑003).
4. k‑fold cross‑validation and bootstrap confidence intervals (SC‑001, SC‑002).
5. Permutation importance with many permutations (FR‑005, FR‑012) and t‑tests (FR‑006).
6. Manifest generation (FR‑007) and markdown report creation (FR‑008).

## 5. Inspect results
- `outputs/report.md` – full analysis, performance metrics, top‑stable features, runtime summary.
- `outputs/manifest.json` – reproducibility record.
- `outputs/model.joblib` – trained model (can be loaded with `joblib.load`).

## 6. Run the test suite (optional)
```bash
pytest -vv
```
All contract‑validation tests must pass; lint warnings must be ≤ 5 (SC‑008).

## 7. Re‑run for stability check
Execute the pipeline three times (e.g., via a loop) and compare the top feature rankings. The maximum rank difference must be ≤ 1 (SC‑006). The quickstart script `scripts/stability_check.sh` automates this.

---
