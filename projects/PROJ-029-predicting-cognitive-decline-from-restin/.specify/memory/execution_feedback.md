# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/01_download_and_filter.py (rc=1); python code/03_compute_graph_metrics.py (rc=1); python code/04_train_model.py (rc=1); 4 declared deliverable(s) absent: data/processed/graph_metrics.csv; data/processed/performance_report.json; data/processed/permutation_results.json

## Failing / missing run-book commands

- python code/01_download_and_filter.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/01_download_and_filter.py", line 345, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/01_download_and_filter.py", line 307, in main
    config = get_config()
             ^^^^^^^^^^
NameError: name 'get_config' is not defined
- python code/03_compute_graph_metrics.py -> rc=1
    2026-07-14 03:05:28,584 - graph_metrics - INFO - Starting graph metrics computation with parallel processing (joblib).
2026-07-14 03:05:28,584 - graph_metrics - ERROR - Failed to load connectivity matrices: Input directory not found: data/processed/connectivity_matrices
- python code/04_train_model.py -> rc=1
    2026-07-14 03:05:29,913 - __main__ - INFO - Starting model training (T023).
2026-07-14 03:05:29,913 - __main__ - ERROR - Graph metrics file not found: data/processed/graph_metrics.csv
2026-07-14 03:05:29,913 - __main__ - ERROR - Please run code/03_compute_graph_metrics.py first.
- python code/05_evaluate_model.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/05_evaluate_model.py", line 27, in <module>
    sys.path.insert(0, str(PROJECT_ROOT / "code"))
                           ^^^^^^^^^^^^
NameError: name 'PROJECT_ROOT' is not defined
- python code/06_permutation_test.py -> rc=1
    2026-07-14 03:05:32,128 - __main__ - INFO - Starting Permutation Test (T029)
2026-07-14 03:05:32,128 - __main__ - ERROR - Model file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl. Run training first.
- python code/07_sensitivity_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 162, in <module>
    def write_outputs(results: Dict[str, Any]) -> None:
                               ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/08_collinearity_check.py -> rc=1
    2026-07-14 03:05:34,184 - 08_collinearity_check - ERROR - Input file not found: data/processed/graph_metrics.csv
2026-07-14 03:05:34,184 - 08_collinearity_check - ERROR - This script requires 'data/processed/graph_metrics.csv' to be generated first by code/03_compute_graph_metrics.py.

## Declared deliverables still missing

- data/processed/graph_metrics.csv
- data/processed/performance_report.json
- data/processed/permutation_results.json
- data/processed/sensitivity_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

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

### `data/processed/eligible_subjects.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/01_download_and_filter.py`, `code/04_train_model.py`, `code/validate_quickstart.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/eligible_subjects.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/01_download_and_filter.py`, `code/06_runtime_verifier.py`, `code/04_train_model.py`, `code/validate_quickstart.py`.

### `data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/08_collinearity_check.py`, `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.

### `data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/08_collinearity_check.py`, `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/graph_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/08_collinearity_check.py`, `code/06_runtime_verifier.py`, `code/03_compute_graph_metrics.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/04_train_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/06_permutation_test.py`, `code/04_train_model.py`, `code/05_evaluate_model.py`, `code/validate_quickstart.py`, `code/07_sensitivity_analysis.py`.
