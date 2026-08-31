# Quickstart: Running the Semantic Collapse Threshold Pipeline

> **Prerequisite**: GitHub Actions runner with Python 3.11. All commands assume execution from the repository root.

## 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Dataset Checksums
```bash
python -m llmxive.utils.checksum verify
```
(Will download the three open ASR datasets and record SHA hashes under `data/checksums.yaml`.)

## 3. Execute the Full Pipeline (CI‑mode)
```bash
python -m llmxive.pipeline \
    --sample-size 5000 \   # reduced sample for CI feasibility (≈ several hundred k jobs)
    --snr-levels -6,-3,0,3,6,9,12,15,18 \
    --rt60-levels 0.2,0.4,0.6,0.8,1.0,1.2 \
    --asr-models whisper-tiny distil-whisper \
    --seed 42 \
    --mode ci
```
The command performs all phases (0–10) defined in `plan.md`. Intermediate artifacts are written to `data/derived/`.

## 4. Execute the Full‑Scale Pipeline (External Compute)
```bash
python -m llmxive.pipeline \
    --sample-size 50000 \   # full study size (≥ 50 000 clips)
    --snr-levels -6,-3,0,3,6,9,12,15,18 \
    --rt60-levels 0.2,0.4,0.6,0.8,1.0,1.2 \
    --asr-models whisper-tiny distil-whisper \
    --seed 42 \
    --mode full
```
- **CI‑mode** runs on the free GitHub Actions runner (2 CPU cores, ≤ 7 GB RAM).  
- **Full‑scale** mode is intended for a Kubernetes/Slurm cluster or a Kaggle GPU off‑load; it will exceed the free‑tier limits and therefore must be launched on external resources.

## 5. Independent US‑3 Verification (Mock Data Test)
```bash
python -m llmxive.pipeline \
    --mock-regression-test true \
    --seed 42
```
This generates a synthetic regression dataset with known interaction effects, trains the same hierarchical model, and checks that the recovered coefficients match the ground‑truth within tolerance. It provides an independent verification of US‑3 without requiring the full stress‑curve generation.

## 6. Inspect Results
```bash
# Stress curves (first 5 rows)
head -n 5 data/derived/stress_curves.parquet | pandasql -c "SELECT * FROM stdin LIMIT 5"

# Collapse points summary
python -c "import pandas as pd; df=pd.read_parquet('data/derived/collapse_points.parquet'); print(df.describe())"

# Regression performance
cat results/regression_summary.json | jq .
```

## 7. Run Unit Tests
```bash
pytest -vv
```
The test suite includes:
- `tests/unit/__init__.py` – ensures the package is importable.
- `tests/unit/test_download.py` – verifies dataset download, checksum validation, and schema compliance (`contracts/dataset.schema.yaml`).
- `tests/unit/test_distort.py` – checks distortion generation, missing‑scenario logging, and `DistortionVector` integrity.
- `tests/unit/test_regression.py` – validates regression input schema (`contracts/regression_input.schema.yaml`) and critical vector output schema (`contracts/critical_vector.schema.yaml`).

All tests are deterministic (seed = 42) and will fail if any required artifact is missing.

## 8. Reproduce the Paper Figures
```bash
jupyter nbconvert --to pdf --execute notebooks/report.ipynb
```
The notebook reads directly from the Parquet artifacts, guaranteeing the *single source of truth* principle.

---



