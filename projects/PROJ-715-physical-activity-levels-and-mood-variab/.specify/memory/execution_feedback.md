# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingest.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingest.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 3 declared deliverable(s) absent: data/processed/daily_aggregates.csv; data/processed/model_results.json; data/raw/bronze.parquet

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
    2026-08-18 07:42:26,206 - INFO - Downloading https://osf.io/download/xxxx-xxxx/ to /home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/raw/bronze.csv
2026-08-18 07:42:26,436 - ERROR - Download failed: 404 Client Error: Not Found for url: https://osf.io/download/xxxx-xxxx/
2026-08-18 07:42:26,437 - ERROR - Failed to download or verify the dataset.
- python code/preprocess.py -> rc=1
    2026-08-18 07:42:26,853 - INFO - Running preprocess.py main
2026-08-18 07:42:26,853 - INFO - Starting preprocessing pipeline
2026-08-18 07:42:26,853 - ERROR - Preprocessing failed: get_path() takes 1 positional argument but 3 were given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 201, in main
    result_df = preprocess()
                ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 172, in preprocess
    df_raw = load_bronze_data()
             ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 27, in load_bronze_data
    path = get_path('data', 'raw', 'bronze.parquet')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 3 were given
- python code/analysis.py -> rc=1
    2026-08-18 07:42:28,517 - INFO - Loading data...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/analysis.py", line 334, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/analysis.py", line 302, in main
    df = load_daily_aggregates()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/analysis.py", line 24, in load_daily_aggregates
    raise FileNotFoundError(f"Daily aggregates file not found at {path}. Run preprocessing first.")
FileNotFoundError: Daily aggregates file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/daily_aggregates.csv. Run preprocessing first.
- python code/report.py -> rc=1
    WARNING:root:matplotlib not found. Some visualization features may be disabled.
ERROR:__main__:Failed to generate report: get_path() takes 1 positional argument but 3 were given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 260, in main
    report_path = generate_report()
                  ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 227, in generate_report
    model_results = load_model_results()
                    ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 30, in load_model_results
    results_path = get_path('data', 'processed', 'model_results.json')
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 3 were given

## Declared deliverables still missing

- data/processed/daily_aggregates.csv
- data/processed/model_results.json
- data/raw/bronze.parquet

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 16 way(s):

- code/output_validator.py: output_path = get_path('data/processed', 'daily_aggregates.csv')
- code/output_validator.py: schema_path = get_path('specs/001-physical-activity-mood-variability/contracts', 'daily_aggregates.schema.yaml')
- code/output_validator.py: log_path = get_path('data/processed', 'validation_log.json')
- code/report.py: results_path = get_path('data', 'processed', 'model_results.json')
- code/report.py: data_path = get_path('data', 'processed', 'daily_aggregates.csv')
- code/report.py: output_dir = get_path('data', 'processed')
- code/ingest.py: raw_data_path = get_path("data/raw/bronze.csv")  # Assuming CSV format
- code/ingest.py: parquet_path = get_path("data/raw/bronze.parquet")
- code/preprocess.py: path = get_path('data', 'raw', 'bronze.parquet')
- code/preprocess.py: output_path = get_path('data', 'processed', 'daily_aggregates.csv')
- code/analysis.py: path = get_path('data/processed/daily_aggregates.csv')
- code/analysis.py: output_path = get_path('data/processed/model_results.json')
- code/save_daily_aggregates.py: input_path = get_path("data", "processed", "daily_aggregates.csv")
- code/save_daily_aggregates.py: schema_path = get_path("specs", "001-physical-activity-mood-variability", "contracts", "daily_aggregates.schema.yaml")
- code/save_results.py: schema_path = get_path("specs/001-physical-activity-levels-and-mood-variability/contracts/model_results.schema.yaml")
- code/save_results.py: output_path = get_path("data/processed/model_results.json")

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/daily_aggregates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/output_validator.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/save_daily_aggregates.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/daily_aggregates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/save_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/bronze.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/bronze.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/daily_aggregates.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/output_validator.py`, `code/report.py`, `code/preprocess.py`, `code/analysis.py`, `code/save_daily_aggregates.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/daily_aggregates.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/output_validator.py`, `code/report.py`, `code/preprocess.py`, `code/analysis.py`, `code/save_daily_aggregates.py`, `code/validate_quickstart.py`.
