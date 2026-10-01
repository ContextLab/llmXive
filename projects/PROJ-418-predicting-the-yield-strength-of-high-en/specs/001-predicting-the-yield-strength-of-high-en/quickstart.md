# Quickstart: Predicting HEA Yield Strength

These steps assume a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

## 1. Clone the repository
```bash
git clone
cd PROJ-418-predicting-the-yield-strength-of-high-en
```

## 2. Set up the environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Run the full pipeline
```bash
python -m src.pipeline.run \
 --seed 42 \
 --output-dir output/
```
- The command downloads real HEA data from the Materials Project API, computes descriptors, performs power analysis, trains the Random Forest, evaluates on both the held‑out test set and an independent external validation set, computes permutation importance, assesses stability, and writes `report.md` and all JSON artifacts to `output/`.

## 4. Inspect the report
```bash
less output/report.md
```
The report contains:
- Dataset statistics & checksum table
- VIF summary
- Power‑analysis justification
- Model performance (R², Pearson r, bootstrap CI)
- Descriptor‑target correlation table (training data)
- Permutation importance with Holm‑Bonferroni corrected p‑values
- Stability ranking comparison across three seeds
- Detailed provenance (including content‑hashes) and measurement‑protocol documentation for primary and external datasets

## 5. Run the CI checks (optional)
```bash
pytest -q
ruff check src/ tests/
black --check src/ tests/
```
All checks must pass (≤ 5 ruff warnings, black formatting clean). The GitHub Actions workflow performs the same steps automatically on each push.
