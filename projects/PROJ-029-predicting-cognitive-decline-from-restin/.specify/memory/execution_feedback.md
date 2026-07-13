# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_download_and_filter.py: synthetic/fake INPUT data not authorized by the spec — “…thout DNS, and we cannot fake data,     we will implement t…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_download_and_filter.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/01_download_and_filter.py: synthetic/fake INPUT data not authorized by the spec — “…thout DNS, and we cannot fake data,     we will implement t…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/06_permutation_test.py; 7 command(s) failed: python code/01_download_and_filter.py (rc=2); python code/02_preprocess_and_parcellate.py (rc=1); python code/03_compute_graph_metrics.py (rc=1); 5 declared deliverable(s) absent: data/processed/eligible_subjects.csv; data/processed/graph_metrics.csv; data/processed/performance_report.json

## Failing / missing run-book commands

- python code/01_download_and_filter.py -> rc=2
    2026-07-13 19:41:18,051 - __main__ - INFO - Starting T017: Download and Filter
2026-07-13 19:41:18,185 - __main__ - ERROR - Failed to check dataset availability: HTTPSConnectionPool(host='api.openneuro.org', port=443): Max retries exceeded with url: /crn/datasets/ds000246/snapshot (Caused by NameResolutionError("HTTPSConnection(host='api.openneuro.org', port=443): Failed to resolve 'api.openneuro.org' ([Errno -2] Name or service not known)"))
2026-07-13 19:41:18,185 - __main__ - ERROR - Dataset ds000246 not available on OpenNeuro.
- python code/02_preprocess_and_parcellate.py -> rc=1
    2026-07-13 19:41:19,644 - preprocess - ERROR - Eligible subjects file not found: data/processed/eligible_subjects.csv
2026-07-13 19:41:19,644 - preprocess - ERROR - Please run 01_download_and_filter.py first
- python code/03_compute_graph_metrics.py -> rc=1
    2026-07-13 19:41:20,279 - graph_metrics - INFO - Starting T035: Graph Metrics Calculation with Parallelization
2026-07-13 19:41:20,279 - graph_metrics - ERROR - Input directory data/processed/adjacency_matrices does not exist.
2026-07-13 19:41:20,279 - graph_metrics - ERROR - Please run code/02_preprocess_and_parcellate.py first.
- python code/04_train_model.py -> rc=1
    Error: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv not found.
- python code/05_evaluate_model.py -> rc=1
    2026-07-13 19:41:21,804 - 05_evaluate_model - INFO - Starting model evaluation (T024).
2026-07-13 19:41:21,804 - 05_evaluate_model - WARNING - CV results file /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/cv_results.json not found. Attempting to re-run training script to generate it.
2026-07-13 19:41:22,968 - 05_evaluate_model - ERROR - Training script failed: Error: /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv not found.

2026-07-13 19:41:22,968 - 05_evaluate_model - ERROR - CRITICAL: Cannot evaluate model without training results.
- python code/06_permutation_test.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/06_permutation_test.py': [Errno 2] No such file or directory
- python code/07_sensitivity_analysis.py -> rc=1
    2026-07-13 19:41:24,163 - __main__ - INFO - Starting Sensitivity Analysis Script (T030a & T030b).
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 342, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 235, in main
    model, X, y, thresholds = load_model_and_data()
                              ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 50, in load_model_and_data
    data_dir = Path(CONFIG['data_processed_dir'])
                    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'data_processed_dir'
- python code/08_collinearity_check.py -> rc=1
    2026-07-13 19:41:25,122 - 08_collinearity_check - ERROR - Input file not found: data/processed/graph_metrics.csv

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
    - `code/04_train_model.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/07_sensitivity_analysis.py` — IS a run-book command
    - `code/02_preprocess_and_parcellate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/eligible_subjects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/12_memory_profiler.py` — NOT invoked by the run-book
    - `code/08_collinearity_check.py` — IS a run-book command
    - `code/15_run_ci_memory_profile.py` — NOT invoked by the run-book
    - `code/06_runtime_verifier.py` — NOT invoked by the run-book
    - `code/14_ci_memory_profiler.py` — NOT invoked by the run-book
    - `code/03_compute_graph_metrics.py` — IS a run-book command
    - `code/04_train_model.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/09_generate_report.py` — IS a run-book command
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
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

### `model.pkl`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[data_processed_dir]`
- PRODUCER(s) to edit: `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`
- CONSUMER(s) that read it: `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`
  → Edit the producer so every required name [data_processed_dir] is in `model.pkl`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/processed/eligible_subjects.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/01_download_and_filter.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/validate_quickstart.py`, `code/02_preprocess_and_parcellate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/eligible_subjects.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/01_download_and_filter.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`, `code/02_preprocess_and_parcellate.py`.

### `data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/08_collinearity_check.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.
