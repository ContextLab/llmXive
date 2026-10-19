# Quickstart: Predicting HEA Yield Strength

These steps assume a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

## 1. Clone the repository
```bash
git clone https://github.com/your-org/PROJ-418-predicting-the-yield-strength-of-high-en.git
cd PROJ-418-predicting-the-yield-strength-of-high-en
```

## 2. Set up the environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run the full pipeline
```bash
python -m src.pipeline.run \
  --seed 42 \
  --output-dir output/
```
The command will:
1. Download real HEA data from the Materials Project API.  
2. Compute deterministic compositional descriptors.  
3. Perform power analysis and VIF handling.  
4. Train a Random Forest with 5‑fold CV.  
5. Evaluate on a held‑out test set and an independent external validation set.  
6. Compute permutation importance (Holm‑Bonferroni corrected).  
7. Run three stability replicates.  
8. Write `output/report.md` and all JSON/YAML artifacts.

## 4. Inspect the report
```bash
less output/report.md
```
The report contains:
- Dataset statistics & checksum table  
- VIF summary  
- Power‑analysis justification  
- Model performance (R², Pearson *r*, bootstrap CI)  
- Descriptor‑target correlation table (training data)  
- Permutation importance with corrected *p*‑values  
- Stability ranking comparison across three seeds  
- Detailed provenance (content‑hashes, seeds, package versions) and measurement‑protocol documentation for primary and external datasets

## 5. Run the CI checks (optional)
```bash
pytest -q
ruff check src/ tests/
black --check src/ tests/
```
All checks must pass (≤ 5 `ruff` warnings, black formatting clean). The GitHub Actions workflow runs the same steps automatically on each push.

---
