# Quickstart: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Prerequisites
* Python 3.11 or newer
* `git`
* Access to the **verified** dataset URLs listed in `research.md`.  
  *If the URLs do not contain the required fMRI or NIH DCCS scores, the pipeline will stop with a clear `gap_report.md`.*

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd <PROJECT_ROOT>

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the End‑to‑End Pipeline

All stages are invoked through `code/main.py`. The script aborts automatically if the data‑gap check fails.

| Step | Command | What it does |
|------|---------|--------------|
| **0. Verify data availability** | `python code/main.py --stage verify_data` | Checks the three verified URLs for required variables; writes `data/gap_report.md` and aborts if data are missing. |
| **1. Download & checksum** | `python code/main.py --stage download` | Streams the parquet/CSV files, stores them under `data/raw/`, records SHA‑256 checksums. |
| **2. Preprocess & parcellate** | `python code/main.py --stage preprocess` | Applies the Schaefer 200‑region atlas, outputs per‑subject time‑series `.npy` files. |
| **3. Quality control** | `python code/main.py --stage quality` | Excludes subjects with Mean FD > 0.2 mm or missing DCCS scores; writes `exclusion_log.csv`. |
| **4. Compute variability metrics** | `python code/main.py --stage features` | Sliding‑window (60 s/1 s) correlation → edge‑wise SD & entropy → Incremental PCA (top 10 components) → `variability_metrics.csv`. |
| **5. Null‑model validation** | `python code/main.py --stage null_model` | Generates phase‑shuffled surrogates, recomputes variability, outputs `null_validation.csv` with `Null_Model_P`. |
| **6. Regression & permutation** | `python code/main.py --stage analysis` | Fits linear model (primary predictor = `PCA_Component_1`) + covariates, runs 10 000 permutations, applies FDR if needed; outputs `regression_summary.json` and `final_results.csv`. |
| **7. Visualisation** | `python code/main.py --stage report` | Creates `variability_vs_flexibility.png` and a short markdown summary. |
| **8. Lint check** | `python code/main.py --stage lint` | Runs `ruff check . > data/logs/ruff.log`; aborts on any error‑level messages. |
| **9. Contract testing** | `pytest -q tests/test_contracts.py` | Validates every output file against the JSON‑Schema contracts. |
| **10. Runtime guard** | (internal) | If any phase exceeds 5 h, the script automatically reduces work (e.g., 5 000 permutations) and logs the adaptation. |

### Example Full Run (assuming data is present)

```bash
python code/main.py --stage verify_data && \
python code/main.py --stage download && \
python code/main.py --stage preprocess && \
python code/main.py --stage quality && \
python code/main.py --stage features && \
python code/main.py --stage null_model && \
python code/main.py --stage analysis && \
python code/main.py --stage report && \
python code/main.py --stage lint && \
pytest -q tests/test_contracts.py
```

If any stage fails, the script exits with a non‑zero status and logs the reason to `data/logs/`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `gap_report.md` created, pipeline stops | Verified URLs lack required fMRI or DCCS scores | No further action; the project cannot proceed without appropriate open data. |
| OOM / MemoryError | Batch size too large for the runner | Reduce `config.BATCH_SIZE` (e.g., `export BATCH_SIZE=10`). |
| Permutation runtime > 5 h | Too many permutations on limited CPU | Set `config.PERMUTATIONS = 5000` in `code/config.py`. |
| Contract test failures | Output file does not match schema | Inspect the failing file; ensure required columns are present and types match the schema. |
| Lint failures (`ruff`) | Code style violations (previous T001) | Review `data/logs/ruff.log` and fix reported issues; re‑run the lint stage. |
| Main script timeout (`exit=-1`) | A phase took longer than the CI limit (previous T002) | The runtime guard will automatically down‑sample work; you can also manually lower batch size or permutation count. |

---
