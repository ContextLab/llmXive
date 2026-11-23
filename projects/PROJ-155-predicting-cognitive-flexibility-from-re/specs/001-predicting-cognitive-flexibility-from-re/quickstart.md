# Quickstart: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Prerequisites
* Python 3.11 or newer
* `git`
* Access to the **verified** dataset URLs listed in `research.md`.  
  *If the URLs do not contain the required fMRI or NIH DCCS scores, the pipeline will stop with a clear `gap_report.md` and no further analysis will be performed.*

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
| **1. Download & checksum** | `python code/main.py --stage download` | Streams the files, stores them under `data/raw/`, records SHA‑256 checksums. |
| **2. Preprocess & parcellate** | `python code/main.py --stage preprocess` | Applies the Schaefer atlas, outputs per‑subject time‑series `.npy` files. |
| **3. Quality control** | `python code/main.py --stage quality` | Excludes subjects with Mean FD > 0.2 mm and subjects missing DCCS scores; writes `exclusion_log.csv`. |
| **4. Compute variability metrics** | `python code/main.py --stage features` | Sliding‑window (30 s, 1 s) correlation → edge‑wise SD & entropy → Incremental PCA (top 10 components) → compute `Motion_Noise_Residual` → outputs `variability_metrics.csv`. |
| **5. Null‑model validation** | `python code/main.py --stage null_model` | Generates 1 000 phase‑shuffled surrogates, recomputes variability, outputs `null_validation.csv` with `Null_Model_P`. |
| **6. Regression & permutation** | `python code/main.py --stage analysis` | Fits linear model (primary predictor = `PCA_Component_1`) + covariates, runs 10 000 permutations, applies FDR if needed; outputs `regression_summary.json` (including `Subject_Results`) and `final_results.csv`. |
| **7. Final result assembly** | `python code/main.py --stage assemble` | Merges subject‑level metrics, null‑model p‑value, motion‑noise residual, inclusion status, and regression results into `final_results.csv` matching `contracts/dataset.schema.yaml`. |
| **8. Contract verification** | `ruff check code/ && pytest -q tests/test_contracts.py` | Runs internal lint (`ruff`) and validates every output file against its JSON‑Schema contracts. |
| **9. Optional visualisation** | `python code/main.py --stage visualise` (optional) | Generates `variability_vs_flexibility.png` (scatter with regression line) for exploratory reporting. |

### Example Full Run (assuming data is present)

```bash
python code/main.py --stage verify_data && \
python code/main.py --stage download && \
python code/main.py --stage preprocess && \
python code/main.py --stage quality && \
python code/main.py --stage features && \
python code/main.py --stage null_model && \
python code/main.py --stage analysis && \
python code/main.py --stage assemble && \
ruff check code/ && pytest -q tests/test_contracts.py
```

If any stage fails, the script exits with a non‑zero status and logs the reason to `data/logs/`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `gap_report.md` created, pipeline stops | Verified URLs lack required fMRI or DCCS scores | No further action; the project cannot proceed without an appropriate open dataset. |
| OOM / MemoryError | Batch size too large for the runner | Reduce `config.BATCH_SIZE` (e.g., `export BATCH_SIZE=10`). |
| Permutation runtime > 5 h | Too many permutations on limited CPU | The runtime guard will automatically reduce to 5 000; you can also set `config.PERMUTATIONS = 5000` in `code/config.py`. |
| Contract test failures | Output file does not match schema | Inspect the failing file; ensure required columns are present and types match the schema. |
| Lint failures (`ruff`) | Code style violations (previous T001) | Review `data/logs/ruff.log` and fix reported issues; re‑run. |
| Main script timeout (`exit=-1`) | A phase took longer than the CI limit (previous T002) | The internal runtime guard will automatically down‑sample work; you can also manually lower batch size or permutation count. |

---



