# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; 5 command(s) failed: python code/01_data_ingestion.py (rc=1); python code/02_preprocessing.py (rc=1); python code/03_correlation_analysis.py (rc=1); 5 declared deliverable(s) absent: data/processed/corpus_clr.parquet; data/processed/correlation_results.csv; data/processed/null_threshold.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=1
2026-10-14 07:33:41 - llmXive_pipeline - INFO - Logging initialized to data/processed/run.log
2026-10-14 07:33:41 - llmXive_pipeline - ERROR - Pipeline failed: enforce_resource_limits() missing 1 required positional argument: 'func'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/01_data_ingestion.py", line 165, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/01_data_ingestion.py", line 141, in main
    enforce_resource_limits()
TypeError: enforce_resource_limits() missing 1 required positional argument: 'func'

- python code/02_preprocessing.py -> rc=1
2026-10-14 07:33:42 - llmXive_pipeline - INFO - Logging initialized to data/processed/run.log

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/02_preprocessing.py", line 272, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/02_preprocessing.py", line 262, in main
    setup_logging()
    ^^^^^^^^^^^^^
NameError: name 'setup_logging' is not defined

- python code/03_correlation_analysis.py -> rc=1
2026-10-14 07:33:43 - llmXive_pipeline - INFO - Logging initialized to data/processed/run.log
2026-10-14 07:33:43 - llmXive_pipeline.__main__ - ERROR - Pipeline failed: enforce_resource_limits() missing 1 required positional argument: 'func'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/03_correlation_analysis.py", line 157, in main
    run_analysis_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/03_correlation_analysis.py", line 105, in run_analysis_pipeline
    enforce_resource_limits()
TypeError: enforce_resource_limits() missing 1 required positional argument: 'func'


- python code/04_predictive_modeling.py -> rc=1
2026-10-14 07:33:44 - llmXive_pipeline - INFO - Logging initialized to data/processed/run.log
2026-10-14 07:33:44 - llmXive_pipeline.__main__ - INFO - Starting Predictive Modeling Pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 252, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 249, in main
    run_modeling_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 220, in run_modeling_pipeline
    features, target = load_preprocessed_data()
                       ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 31, in load_preprocessed_data
    raise FileNotFoundError(f"Required data file not found: {data_path}")
FileNotFoundError: Required data file not found: data/processed/corpus_clr.parquet

- python code/05_sensitivity_analysis.py -> rc=1
2026-10-14 07:33:45 - llmXive_pipeline - INFO - Logging initialized to data/processed/run.log
2026-10-14 07:33:45 - llmXive_pipeline.__main__ - INFO - Starting Sensitivity Analysis

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/05_sensitivity_analysis.py", line 202, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/05_sensitivity_analysis.py", line 199, in main
    run_sensitivity_analysis()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/05_sensitivity_analysis.py", line 191, in run_sensitivity_analysis
    results_df = sweep_rarefaction_depths(depths)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/05_sensitivity_analysis.py", line 75, in sweep_rarefaction_depths
    set_random_seed(seed)
TypeError: set_random_seed() takes 0 positional arguments but 1 was given

- python code/run_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-189-investigating-the-correlation-between-gu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/run_pipeline.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/corpus_clr.parquet
- data/processed/correlation_results.csv
- data/processed/null_threshold.json
- data/processed/sensitivity_variance_report.json
- data/processed/significance_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/corpus_clr.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/04_predictive_modeling.py` — IS a run-book command
    - `code/04_predictive_modeling_optimized.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corpus_clr.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/04_extract_discussion.py` — NOT invoked by the run-book
    - `code/04_extract_results.py` — NOT invoked by the run-book
    - `code/04_write_discussion.py` — NOT invoked by the run-book
    - `code/05_write_paper_results.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/null_threshold.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_results.py` — NOT invoked by the run-book
    - `code/04_predictive_modeling.py` — IS a run-book command
    - `code/04_predictive_modeling_optimized.py` — NOT invoked by the run-book
    - `code/04_verify_model_significance.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_threshold.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_variance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_write_discussion.py` — NOT invoked by the run-book
    - `code/05_sensitivity_analysis.py` — IS a run-book command
    - `code/05_sensitivity_analysis_optimized.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_variance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/significance_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_extract_results.py` — NOT invoked by the run-book
    - `code/04_write_discussion.py` — NOT invoked by the run-book
    - `code/05_write_paper_results.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/significance_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
