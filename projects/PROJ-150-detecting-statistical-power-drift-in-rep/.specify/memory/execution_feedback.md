# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download_data.py (rc=1); python -m code.run_pipeline (rc=1); python -m pytest tests/ (rc=1); 5 declared deliverable(s) absent: data/derived/cleaned_data.csv; data/derived/grouping_validation.json; data/derived/residuals.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
ROR - `trust_remote_code` is not supported anymore.
Please check that the Hugging Face dataset 'osf/reproducibility_project' isn't based on a loading script and remove `trust_remote_code`.
If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.
2026-10-10 21:11:52,715 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/osf/reproducibility_project/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-10 21:11:52,716 - ERROR - Dataset osf/reproducibility_project not found or inaccessible: Dataset 'osf/reproducibility_project' doesn't exist on the Hub or cannot be accessed.
2026-10-10 21:11:52,716 - ERROR - Data fetch failed: Real data source unavailable: osf/reproducibility_project. Error: Dataset 'osf/reproducibility_project' doesn't exist on the Hub or cannot be accessed.

`trust_remote_code` is not supported anymore.
Please check that the Hugging Face dataset 'osf/reproducibility_project' isn't based on a loading script and remove `trust_remote_code`.
If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.

- python -m code.run_pipeline -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/.venv/bin/python: No module named code.run_pipeline

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/derived/cleaned_data.csv
- data/derived/grouping_validation.json
- data/derived/residuals.csv
- data/derived/schema_validation.json
- data/raw/data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_fit.py` — NOT invoked by the run-book
    - `code/preprocess.py` — NOT invoked by the run-book
    - `code/robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/grouping_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_fit.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/preprocess.py` — NOT invoked by the run-book
    - `code/verify_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/grouping_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/residuals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_fit.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/visualize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/residuals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/schema_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_data.py` — IS a run-book command
    - `code/validate_schema.py` — NOT invoked by the run-book
    - `code/validate_source.py` — NOT invoked by the run-book
    - `code/verify_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/schema_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_drift.py` — NOT invoked by the run-book
    - `code/compute_trends.py` — NOT invoked by the run-book
    - `code/download.py` — NOT invoked by the run-book
    - `code/download_data.py` — IS a run-book command
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/logging_config.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/model_fit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
