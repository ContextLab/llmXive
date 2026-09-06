# Quickstart: Predicting HEA Yield Strength

The following steps assume a fresh GitHub Actions runner (or local environment with the same specs).

## 1. Clone the Repository
```bash
git clone
cd heal-predictor
```

## 2. Set Up the Python Environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Run the Full Pipeline
```bash
python -m src
```
The command executes all phases in order:
1. Data download & validation
2. Descriptor calculation & VIF handling
3. Power analysis
4. Model training (5‑fold CV)
5. Internal evaluation + bootstrap CI
6. Correlation analysis
7. Permutation importance + Holm‑Bonferroni test
8. (Optional) External validation
9. Report generation (`output/report.md`)
10. Linting & CI summary (`output/pipeline_runtime.json`)

## 4. Inspect Results
- **Report**: `output/report.md`
- **Metrics JSON**: `output/metrics.json`
- **Importance JSON**: `output/importance.json`
- **Manifest**: `output/manifest.json`

## 5. Run Tests (optional)
```bash
pytest -vv
```

## 6. CI Execution
Push any commit to `main`; the GitHub Actions workflow (`.github/workflows/ci.yml`) will automatically run the same pipeline, enforce linting, and verify schema compliance.

---
