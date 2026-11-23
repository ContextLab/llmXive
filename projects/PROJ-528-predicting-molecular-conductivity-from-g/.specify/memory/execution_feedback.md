# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/descriptors.csv: column(s) homo_lumo_gap are EMPTY in every one of 2 rows — that measure was never recorded
- data/processed/filtered_train.csv: header only, ZERO data rows — the analysis produced no rows
- data/processed/quantum_proxy_report.json: metric is null/NaN (homo_lumo_column) — not a real measurement
- every produced artifact is gitignored (data/processed/analysis_summary.json, data/processed/corr_plot_top5.png, data/processed/descriptors.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/descriptors.csv: column(s) homo_lumo_gap are EMPTY in every one of 2 rows — that measure was never recorded; data/processed/filtered_train.csv: header only, ZERO data rows — the analysis produced no rows; data/processed/quantum_proxy_report.json: metric is null/NaN (homo_lumo_column) — not a real measurement; every produced artifact is gitignored (data/processed/analysis_summary.json, data/processed/corr_plot_top5.png, data/processed/descriptors.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/main.py (rc=1); python -m pytest tests/unit/ (rc=1); python -m pytest tests/integration/ (rc=4); 1 declared deliverable(s) absent: data/processed/model_results.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
ance written to /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/data/processed/feature_importance.csv
2026-10-12 10:09:37,164 INFO code.feature_importance: Feature importance summary written to /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/data/processed/feature_importance_summary.json
2026-10-12 10:09:37,164 INFO __main__: Step 7: Generating plots...
2026-10-12 10:09:37,273 INFO code.plotting: Placeholder plot saved to /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/data/processed/corr_plot_top5.png
2026-10-12 10:09:37,273 INFO __main__: Step 8: Generating analysis summary...
2026-10-12 10:09:37,275 INFO code.analysis_summary: Analysis summary written to /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/data/processed/analysis_summary.json
2026-10-12 10:09:37,275 INFO __main__: Pipeline completed in 12.86 seconds.
2026-10-12 10:09:37,276 ERROR __main__: Missing output files: ['/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/data/processed/model_results.json']

- python -m pytest tests/unit/ -> rc=1
===== short test summary info ============================
FAILED tests/unit/test_descriptors.py::test_benzene_descriptors - KeyError: '...
FAILED tests/unit/test_descriptors.py::test_butadiene_conjugation_length - as...
FAILED tests/unit/test_descriptors.py::test_ethanol_descriptors - KeyError: '...
FAILED tests/unit/test_preprocessing_dynamic_range.py::test_compute_dynamic_range_failure_nonpositive
FAILED tests/unit/test_preprocessing_dynamic_range.py::test_preprocessing_main_fails_when_range_too_small
FAILED tests/unit/test_preprocessing_exclusion.py::test_invalid_descriptors_counted
FAILED tests/unit/test_preprocessing_exclusion.py::test_clean_rows_are_valid
FAILED tests/unit/test_statistics.py::test_apply_bh_to_df - assert True is True
FAILED tests/unit/test_t013_descriptors.py::TestDescriptors::test_benzene_aromaticity
FAILED tests/unit/test_t013_descriptors.py::TestDescriptors::test_butadiene_conjugation
FAILED tests/unit/test_t013_descriptors.py::TestDescriptors::test_at_least_ten_numeric_descriptor_values
FAILED tests/unit/test_t013_descriptors.py::TestDescriptors::test_homo_lumo_passthrough
================== 12 failed, 38 passed, 13 warnings in 2.31s ==================


- python -m pytest tests/integration/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.0.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/



## Declared deliverables still missing

- data/processed/model_results.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **8999964** real records with fields: smiles.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from datasets import load_dataset
# Load the PubChem-10M-Canonicalized dataset from Hugging Face
# This dataset is memory-mapped, so len() is fast even for 10M records
ds = load_dataset('sagawa/pubchem-10m-canonicalized', split='train')
print(f'RECORDS={len(ds)}')
print(f'FIELDS=smiles')
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/run_analysis.py` — NOT invoked by the run-book
    - `code/run_finalize_results.py` — NOT invoked by the run-book
    - `code/run_huckel_vif_loop.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/run_validation_task.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
