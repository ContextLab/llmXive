# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_data_ingestion.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; 5 command(s) failed: python code/01_data_ingestion.py (rc=1); python code/02_preprocessing.py (rc=1); python code/03_correlation_analysis.py (rc=1); 5 declared deliverable(s) absent: data/processed/corpus_clr.parquet; data/processed/correlation_results.csv; data/processed/null_threshold.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=1
line 1786, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'qiita/16s_gut_microbiome' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/01_data_ingestion.py", line 144, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/01_data_ingestion.py", line 128, in main
    agp_df = fetch_agp_data(agp_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/01_data_ingestion.py", line 42, in fetch_agp_data
    raise DataFetchError(f"Failed to fetch AGP data from real source: {e}")
utils.data_fetchers.DataFetchError: Failed to fetch AGP data from real source: Dataset 'qiita/16s_gut_microbiome' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

- python code/02_preprocessing.py -> rc=1
oundError(f"Merged data file not found at {MERGED_DATA_PATH}. "
FileNotFoundError: Merged data file not found at data/processed/merged_dataset.parquet. Run data ingestion pipeline first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/02_preprocessing.py", line 242, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/02_preprocessing.py", line 235, in main
    result = run_preprocessing_pipeline()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/02_preprocessing.py", line 166, in run_preprocessing_pipeline
    df = load_merged_data()
         ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/02_preprocessing.py", line 27, in load_merged_data
    raise FileNotFoundError(f"Merged data file not found at {MERGED_DATA_PATH}. "
FileNotFoundError: Merged data file not found at data/processed/merged_dataset.parquet. Run data ingestion pipeline first.

- python code/03_correlation_analysis.py -> rc=1
5 08:12:48 - llmXive_pipeline.__main__ - ERROR - Pipeline failed: Preprocessed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/data/processed/rarefied_genus_table.parquet. Run preprocessing first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/03_correlation_analysis.py", line 138, in main
    run_analysis_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/03_correlation_analysis.py", line 100, in run_analysis_pipeline
    df = load_preprocessed_data()
         ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/03_correlation_analysis.py", line 29, in load_preprocessed_data
    raise FileNotFoundError(f"Preprocessed data not found at {input_path}. Run preprocessing first.")
FileNotFoundError: Preprocessed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/data/processed/rarefied_genus_table.parquet. Run preprocessing first.


- python code/04_predictive_modeling.py -> rc=1
2026-10-15 08:12:49 - llmXive_pipeline - INFO - Logging initialized to data/processed/run.log
2026-10-15 08:12:49 - llmXive_pipeline.__main__ - INFO - Starting Predictive Modeling Pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 237, in main
    run_modeling_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 208, in run_modeling_pipeline
    features, target = load_preprocessed_data()
                       ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/04_predictive_modeling.py", line 31, in load_preprocessed_data
    raise FileNotFoundError(f"Required data file not found: {data_path}")
FileNotFoundError: Required data file not found: data/processed/corpus_clr.parquet

- python code/05_sensitivity_analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/05_sensitivity_analysis.py", line 15, in <module>
    from config import get_config, set_random_seed
ImportError: cannot import name 'get_config' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-189-investigating-the-correlation-between-gu/code/config.py)

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
    - `code/03_correlation_analysis.py` — IS a run-book command
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
