# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: python code/main.py --task generate --output data/raw/traces --seed 42 --count [deferred] (rc=1); python code/main.py --task validate_integrity --input data/raw/traces (rc=1); python code/main.py --task extract --input data/raw/traces --output data/processed/metrics.csv (rc=1); 8 declared deliverable(s) absent: data/processed/accuracy_deltas.csv; data/processed/aggregate_model_summary.json; data/processed/benchmark_results.json

## Failing / missing run-book commands

- python code/main.py --task generate --output data/raw/traces --seed 42 --count [deferred] -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task validate_integrity --input data/raw/traces -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task extract --input data/raw/traces --output data/processed/metrics.csv -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task train --input data/processed/metrics.csv --split training --output data/processed/rules/model.json -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task benchmark --rules data/processed/rules/model.json --test-set data/held_out/ --output data/processed/results/summary.json -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task analyze --input data/processed/results/summary.json --metrics data/processed/metrics.csv --output data/processed/statistical_analysis_results.json -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task sensitivity --rules data/processed/rules/model.json --output data/processed/sensitivity_report.json -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task feasibility --output data/processed/feasibility_report.json -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python code/main.py --task report --input data/processed/ --output data/processed/final_report.md -> rc=1
=== llmXive Pipeline Pre-Flight Checks ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a
Data Root: /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data

[PASS] OK: Training Set (data/training/) found with 5000 files.
[PASS] OK: Held-Out Set (data/held_out/) found with 5001 files.
[FAIL] Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

--- PRE-FLIGHT FAILED ---
The following required artifacts are missing or invalid:
  - Path is not a file: Feature Matrix (data/processed/feature_matrix.csv) at '/home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/data/processed/feature_matrix.csv'

Please ensure the following tasks have completed successfully:
  - T012: Synthetic Trace Generation (data/raw/)
  - T012b: Dataset Splitting (data/training/, data/held_out/)
  - T020b: Metric Extraction (data/processed/feature_matrix.csv)


Error: Pre-flight checks failed. Aborting pipeline execution.

- python -m pytest tests/ -> rc=2
work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/code/contracts/__init__.py)
___________ ERROR collecting unit/test_measure_retrieval_latency.py ____________
import file mismatch:
imported module 'test_measure_retrieval_latency' has this __file__ attribute:
  /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/tests/evaluation/test_measure_retrieval_latency.py
which is not the same as the test file we want to collect:
  /home/runner/work/llmXive/llmXive/projects/PROJ-859-llmxive-follow-up-extending-memslides-a/tests/unit/test_measure_retrieval_latency.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
=========================== short test summary info ============================
ERROR tests/test_linting_config.py
ERROR tests/unit/test_calculate_compression_ratio.py
ERROR tests/unit/test_compressibility_score.py
ERROR tests/unit/test_contract_validation.py
ERROR tests/unit/test_measure_retrieval_latency.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 1.28s ===============================



## Declared deliverables still missing

- data/processed/accuracy_deltas.csv
- data/processed/aggregate_model_summary.json
- data/processed/benchmark_results.json
- data/processed/data_lineage.json
- data/processed/feature_matrix.csv
- data/processed/sensitivity_sweep.csv
- data/processed/split_validation.json
- data/processed/statistical_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/accuracy_deltas.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/evaluation/calculate_deltas.py` — NOT invoked by the run-book
    - `code/evaluation/stats.py` — NOT invoked by the run-book
    - `code/utils/lineage.py` — NOT invoked by the run-book
    - `code/utils/loaders.py` — NOT invoked by the run-book
    - `code/validation/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/accuracy_deltas.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aggregate_model_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aggregate_model_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/benchmark_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/agents/benchmark_runner.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/contracts/__init__.py` — NOT invoked by the run-book
    - `code/evaluation/benchmark.py` — NOT invoked by the run-book
    - `code/evaluation/calculate_deltas.py` — NOT invoked by the run-book
    - `code/evaluation/final_report_generator.py` — NOT invoked by the run-book
    - `code/utils/lineage.py` — NOT invoked by the run-book
    - `code/validation/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/benchmark_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/data_lineage.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/final_report_generator.py` — NOT invoked by the run-book
    - `code/utils/lineage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/data_lineage.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/generate_feature_matrix.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/evaluation/final_report_generator.py` — NOT invoked by the run-book
    - `code/evaluation/stats.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/metrics/extract.py` — NOT invoked by the run-book
    - `code/models/rule_induction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/evaluation/final_report_generator.py` — NOT invoked by the run-book
    - `code/evaluation/sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/utils/lineage.py` — NOT invoked by the run-book
    - `code/validation/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/run_validation_proxy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/split_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/evaluation/final_report_generator.py` — NOT invoked by the run-book
    - `code/evaluation/stats.py` — NOT invoked by the run-book
    - `code/utils/lineage.py` — NOT invoked by the run-book
    - `code/validation/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
