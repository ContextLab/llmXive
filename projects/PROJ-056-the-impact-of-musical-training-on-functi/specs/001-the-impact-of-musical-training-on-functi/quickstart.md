# Quickstart: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Prerequisites
- Python 3.11+
- ~a few GB free RAM (a ceiling enforced by the pipeline)
- Git

## 2. Installation
```bash
git clone <REPO_URL>
cd projects/PROJ-056-the-impact-of-musical-training-on-functi
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### 3.1 Synthetic Verification Mode (default)
```bash
python code/main.py --mode synthetic --n-subjects 100 --seed 42
```
Generates a mock cohort (with seeded missingness/corruption so the inclusion audit is exercised), computes connectivity and network metrics, runs all statistical tests, and writes results under `data/processed/`. **Synthetic mode validates the pipeline only** — it contains no real group effect and supports no scientific conclusion about musical training.

Individual stages can be run directly:
```bash
python code/data/run_synthetic_generator.py --n-subjects 100 --seed 42
```

### 3.2 Real‑Data Mode (when a verified dataset becomes available)
```bash
python code/main.py --mode real --data-path /path/to/verified/dataset
```
The directory must contain `subjects.csv` with the exact Subject‑schema columns and the NIfTI files referenced by `rs_fmri_path`. If no path is supplied or files are missing, the pipeline exits gracefully with a clear "data source unavailable" message and a JSON status file — it never hangs or returns partial data.

### 3.3 Smoke test
```bash
python code/run_quickstart_test.py
```
Runs the quickstart commands end‑to‑end and validates every output against its JSON‑Schema contract.

## 4. Verify Outputs
```bash
pytest tests/
cat data/logs/memory_usage.log
```

## 5. Interpreting Results
- `data/processed/network_metrics/` — per‑subject mean within‑network connectivity (auditory/motor/executive).
- `data/results/statistical_results.csv` — edge‑wise Welch's t‑tests; `q_value < 0.05`.
- `data/results/nbs_components.json` — largest component; check `p_value_fwer`.
- `data/results/sensitivity_analysis.csv` — significant‑edge counts at q = 0.01/0.05/0.10.
- `data/results/results_summary.csv` — single source of truth aggregating all primary outcomes.

## 6. Troubleshooting
- **Memory pressure** — the pipeline streams per subject and, if a step still approaches the defined memory threshold, automatically applies deterministic seeded subsetting (logged) to comply with FR‑006; a hard abort occurs only if subsetting cannot bring usage below the limit.
- **"Sample Size Insufficient"** — fewer than 50 subjects per group after filtering (the log also records the equivalent "Insufficient Data for Power" phrasing); expected behavior, not a bug.
- **Real‑data mode reports unavailability** — no verified dataset is configured; this is the documented current state, not an error to work around.
- **Long runtime** — reduce `--n-permutations` (minimum 500 for exploratory runs).
