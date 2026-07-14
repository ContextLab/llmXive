# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_download_and_filter.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/01_download_and_filter.py (rc=2); python code/03_compute_graph_metrics.py (rc=1); python code/04_train_model.py (rc=1); 5 declared deliverable(s) absent: data/processed/eligible_subjects.csv; data/processed/graph_metrics.csv; data/processed/performance_report.json

## Failing / missing run-book commands

- python code/01_download_and_filter.py -> rc=2
    2026-07-14 07:17:32,789 - 01_download_and_filter - INFO - Starting T017: Download and Filter
2026-07-14 07:17:32,971 - 01_download_and_filter - ERROR - Network error checking dataset availability: HTTPSConnectionPool(host='api.openneuro.org', port=443): Max retries exceeded with url: /datasets/ds000246 (Caused by NameResolutionError("HTTPSConnection(host='api.openneuro.org', port=443): Failed to resolve 'api.openneuro.org' ([Errno -2] Name or service not known)"))
- python code/03_compute_graph_metrics.py -> rc=1
    2026-07-14 07:17:33,690 - graph_metrics - INFO - Starting T035: Compute Graph Metrics (Parallel Optimized)
2026-07-14 07:17:33,690 - graph_metrics - ERROR - Subject list not found: data/processed/eligible_subjects.csv
- python code/04_train_model.py -> rc=1
    2026-07-14 07:17:34,776 - 04_train_model - INFO - Starting T023: Train Model with Nested CV
2026-07-14 07:17:34,776 - 04_train_model - INFO - Loading graph metrics from data/processed/graph_metrics.csv
2026-07-14 07:17:34,776 - 04_train_model - ERROR - Graph metrics file not found: data/processed/graph_metrics.csv
2026-07-14 07:17:34,776 - 04_train_model - ERROR - Please run code/03_compute_graph_metrics.py first.
- python code/05_evaluate_model.py -> rc=1
    2026-07-14 07:17:35,150 - evaluate_model - INFO - Starting T024: Evaluate Model
2026-07-14 07:17:35,150 - evaluate_model - INFO - Model path: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl
2026-07-14 07:17:35,150 - evaluate_model - INFO - Output path: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/performance_report.json
2026-07-14 07:17:35,150 - evaluate_model - INFO - Graph metrics path: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv
2026-07-14 07:17:35,151 - evaluate_model - ERROR - Graph metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv
2026-07-14 07:17:35,151 - evaluate_model - ERROR - Graph metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv
- python code/06_permutation_test.py -> rc=1
    2026-07-14 07:17:35,999 - __main__ - INFO - Starting Permutation Test (T029)
2026-07-14 07:17:35,999 - __main__ - ERROR - Model file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl. Run training first.
- python code/07_sensitivity_analysis.py -> rc=1
    2026-07-14 07:17:36,941 - 07_sensitivity_analysis - INFO - Starting T030b: Sensitivity Analysis (Part 2)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 332, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 321, in main
    df, X, y_base = load_model_and_data(logger)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 62, in load_model_and_data
    metrics_path = Path(config["data"]["processed"]) / "graph_metrics.csv"
                        ~~~~~~^^^^^^^^
KeyError: 'data'
- python code/08_collinearity_check.py -> rc=1
    2026-07-14 07:17:37,724 - 08_collinearity_check - ERROR - Input file not found: data/processed/graph_metrics.csv
2026-07-14 07:17:37,724 - 08_collinearity_check - ERROR - This script requires 'data/processed/graph_metrics.csv' to be generated first by code/03_compute_graph_metrics.py.

## Declared deliverables still missing

- data/processed/eligible_subjects.csv
- data/processed/graph_metrics.csv
- data/processed/performance_report.json
- data/processed/permutation_results.json
- data/processed/sensitivity_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/eligible_subjects.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_and_filter.py` — IS a run-book command
    - `code/06_runtime_verifier.py` — NOT invoked by the run-book
    - `code/03_compute_graph_metrics.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/eligible_subjects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/12_memory_profiler.py` — NOT invoked by the run-book
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/08_collinearity_check.py` — IS a run-book command
    - `code/15_run_ci_memory_profile.py` — NOT invoked by the run-book
    - `code/15_ci_memory_profiler.py` — NOT invoked by the run-book
    - `code/06_runtime_verifier.py` — NOT invoked by the run-book
    - `code/14_ci_memory_profiler.py` — NOT invoked by the run-book
    - `code/03_compute_graph_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/09_generate_report.py` — IS a run-book command
    - `code/03_compute_graph_metrics.py` — IS a run-book command
    - `code/04_train_model.py` — IS a run-book command
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/09_generate_report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/09_generate_report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/07_sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `graph_metrics.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[data]`
- PRODUCER(s) to edit: `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/validate_quickstart.py`
- CONSUMER(s) that read it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`
  → Edit the producer so every required name [data] is in `graph_metrics.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/processed/eligible_subjects.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/01_download_and_filter.py`, `code/03_compute_graph_metrics.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/eligible_subjects.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/01_download_and_filter.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/validate_quickstart.py`.

### `data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.

### `data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`.
