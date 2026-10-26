# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/descriptor_names.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/descriptor_names.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/main.py --step fetch_and_preprocess (rc=-1); python code/main.py --step feature_selection (rc=1); python code/main.py --step train (rc=1); 1 declared deliverable(s) absent: data/processed/cluster_map.csv

## Failing / missing run-book commands

- python code/main.py --step fetch_and_preprocess -> rc=-1
2026-10-26 15:33:26,951 - main - INFO - Starting pipeline...
2026-10-26 15:33:26,952 - main - INFO - Running data preprocessing (descriptor generation)...
2026-10-26 15:33:26,952 - data.generate_descriptors - INFO - Found 412 total RDKit descriptors, 326 after filtering.
2026-10-26 15:33:26,952 - data.generate_descriptors - INFO - Descriptor names written to /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/processed/descriptor_names.json
2026-10-26 15:33:26,952 - data.generate_descriptors - INFO - Loading QM9 dataset via qm9pack...
2026-10-26 15:33:56,366 - data.generate_descriptors - INFO - Processed 5000 records – Current RSS 513.2 MiB
2026-10-26 15:34:25,112 - data.generate_descriptors - INFO - Processed 10000 records – Current RSS 594.3 MiB
2026-10-26 15:34:54,342 - data.generate_descriptors - INFO - Processed 15000 records – Current RSS 674.7 MiB
2026-10-26 15:35:25,081 - data.generate_descriptors - INFO - Processed 20000 records – Current RSS 755.8 MiB


[TIMEOUT after 120s]
- python code/main.py --step feature_selection -> rc=1
2026-10-26 15:35:26,988 - main - INFO - Starting pipeline...
2026-10-26 15:35:26,988 - main - INFO - Running feature selection (VIF pruning & clustering)...
2026-10-26 15:35:26,988 - main - ERROR - Feature selection module not found (data/feature_selection.py).
2026-10-26 15:35:26,988 - main - ERROR - Pipeline failed.


- python code/main.py --step train -> rc=1
2026-10-26 15:35:27,637 - main - INFO - Starting pipeline...
2026-10-26 15:35:27,637 - main - ERROR - Training step not yet implemented.
2026-10-26 15:35:27,637 - main - ERROR - Pipeline failed.


- python code/main.py --step analyze -> rc=1
2026-10-26 15:35:28,287 - main - INFO - Starting pipeline...
2026-10-26 15:35:28,287 - main - ERROR - Analysis step not yet implemented.
2026-10-26 15:35:28,287 - main - ERROR - Pipeline failed.


- python code/main.py --step verify -> rc=1
2026-10-26 15:35:28,932 - main - INFO - Starting pipeline...
2026-10-26 15:35:28,932 - main - INFO - Validating artifact integrity (checksums)...
2026-10-26 15:35:28,932 - main - ERROR - Manifest missing 'checksums' key.
2026-10-26 15:35:28,932 - main - ERROR - Pipeline failed.


- python -m pytest tests/ -v -> rc=2
tests/integration/test_full_pipeline.py:34: in <module>
    from models.train_lightgbm import train_lightgbm_model
E   ImportError: cannot import name 'train_lightgbm_model' from 'models.train_lightgbm' (/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/models/train_lightgbm.py)
=============================== warnings summary ===============================
tests/contract/validators.py:55
  /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/contract/validators.py:55: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    class DescriptorMatrix(BaseModel):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 1.82s ==========================



## Declared deliverables still missing

- data/processed/cluster_map.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cluster_map.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/feature_clustering.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/models/generate_shap_report.py` — NOT invoked by the run-book
    - `code/models/generate_stability_report.py` — NOT invoked by the run-book
    - `code/models/interpret.py` — NOT invoked by the run-book
    - `code/models/stability_analysis.py` — NOT invoked by the run-book
    - `code/utils/checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_map.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
