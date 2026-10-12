# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sparsity_sampling.py --levels 5 10 20 30 40 50 100 --seeds 42 123 456; 5 command(s) failed: python code/data_ingestion.py (rc=1); python code/test_split.py (rc=1); python code/model_training.py (rc=1); 10 declared deliverable(s) absent: data/metadata/raw_pool_checksum.json; data/processed/descriptors_pool.csv; data/processed/filtered_pool.csv

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1
2026-10-12 01:51:01,301 - __main__ - INFO - Starting data ingestion pipeline...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/data_ingestion.py", line 391, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/data_ingestion.py", line 352, in main
    config = load_env_config()
             ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/data_ingestion.py", line 26, in load_env_config
    raise RuntimeError("MP_API_KEY environment variable is missing. Cannot proceed.")
RuntimeError: MP_API_KEY environment variable is missing. Cannot proceed.

- python code/test_split.py -> rc=1
2026-10-12 01:51:01,643 - __main__ - ERROR - Runtime Error: CRITICAL: Input file data/raw/raw_pool.csv does not exist. Task T024 (data ingestion) must complete successfully before T020 can run. Do not generate synthetic data.


- python code/sparsity_sampling.py --levels 5 10 20 30 40 50 100 --seeds 42 123 456 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-458-quantifying-the-impact-of-dataset-sparsi/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/sparsity_sampling.py': [Errno 2] No such file or directory

- python code/model_training.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/model_training.py", line 326, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/model_training.py", line 218, in main
    load_env()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/config.py", line 45, in load_env
    raise RuntimeError(
RuntimeError: MP_API_KEY environment variable is required but not set. Create a .env file (see .env.example) or export the variable in your shell before running any pipeline script.

- python code/statistical_analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/statistical_analysis.py", line 378, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/statistical_analysis.py", line 341, in main
    metrics_df = load_metrics(args.metrics)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/code/statistical_analysis.py", line 35, in load_metrics
    raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
FileNotFoundError: Metrics file not found at data/results/metrics.csv

- python -m pytest tests/integration/test_pipeline.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.3, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi
plugins: platformdirs-4.13.0, cov-4.1.0
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_pipeline.py



## Declared deliverables still missing

- data/metadata/raw_pool_checksum.json
- data/processed/descriptors_pool.csv
- data/processed/filtered_pool.csv
- data/processed/full_pool_final.csv
- data/processed/rss_pool.csv
- data/processed/test_set.csv
- data/processed/test_set_indices.csv
- data/raw/raw_pool.csv
- data/results/ingestion_log.json
- data/results/metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/raw_pool_checksum.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/metadata/raw_pool_checksum.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors_pool.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/descriptors_pool.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_pool.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_pool.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/full_pool_final.csv` is declared but was NOT written. Scripts referencing it:
    - `code/checksum_pool.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/model_training.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
    - `code/validate_stratification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/full_pool_final.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/rss_pool.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
    - `code/validate_stratification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/rss_pool.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/model_training.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
    - `code/test_split.py` — IS a run-book command
    - `code/verify_test_set.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_set_indices.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
    - `code/test_split.py` — IS a run-book command
    - `code/verify_test_set.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_set_indices.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/raw_pool.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
    - `code/test_split.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/raw_pool.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/ingestion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/results/ingestion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — IS a run-book command
    - `code/sparsity_generation.py` — NOT invoked by the run-book
    - `code/statistical_analysis.py` — IS a run-book command
    - `code/utils/metrics_io.py` — NOT invoked by the run-book
    - `code/validate_stratification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
