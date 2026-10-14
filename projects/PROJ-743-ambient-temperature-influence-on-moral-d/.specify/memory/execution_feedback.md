# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json (rc=1); python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet (rc=1); python code/preprocessing.py --input data/processed/merged_dataset.parquet --output data/processed/cleaned_dataset.parquet (rc=1); 1 declared deliverable(s) absent: data/processed/merged_dataset.parquet

## Failing / missing run-book commands

- python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json -> rc=1
2026-10-14 07:13:01,616 - data_quality - WARNING - Moral Machine file not found at data/raw/moral_machine.csv. Attempting download.
2026-10-14 07:13:01,616 - data_quality - INFO - Starting download of Moral Machine dataset from https://raw.githubusercontent.com/ethical-ai/moral-machine/master/data/processed/moral_machine.csv
2026-10-14 07:13:01,707 - data_quality - ERROR - Failed to download Moral Machine dataset: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/ethical-ai/moral-machine/master/data/processed/moral_machine.csv
2026-10-14 07:13:01,707 - data_quality - ERROR - Automatic download failed: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/ethical-ai/moral-machine/master/data/processed/moral_machine.csv
2026-10-14 07:13:01,707 - data_quality - INFO - Validation report written to results/logs/validation_report.json


- python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet -> rc=1
2026-10-14 07:13:02,112 - ingestion - INFO - Starting ingestion pipeline
2026-10-14 07:13:02,112 - ingestion - INFO - Input: --input
2026-10-14 07:13:02,112 - ingestion - INFO - Output: --temp
2026-10-14 07:13:02,112 - ingestion - INFO - Loading Moral Machine data from --input
2026-10-14 07:13:02,112 - ingestion - ERROR - Ingestion pipeline failed: Input file not found: --input
2026-10-14 07:13:02,112 - data_quality - ERROR - Ingestion pipeline failed: Input file not found: --input

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/ingestion.py", line 282, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/ingestion.py", line 226, in main
    df = load_moral_machine_data(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/ingestion.py", line 58, in load_moral_machine_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: --input

- python code/preprocessing.py --input data/processed/merged_dataset.parquet --output data/processed/cleaned_dataset.parquet -> rc=1
2026-10-14 07:13:02,508 - preprocessing - INFO - Starting T033d: Compute Temperature-Adjusted Response Times
2026-10-14 07:13:02,509 - preprocessing - INFO - Input: data/processed/merged_dataset.parquet
2026-10-14 07:13:02,509 - preprocessing - INFO - Output: data/processed/cleaned_dataset.parquet
2026-10-14 07:13:02,518 - preprocessing - ERROR - Failed to load input dataset: [Errno 2] No such file or directory: 'data/processed/merged_dataset.parquet'


- python code/modeling.py --input data/processed/cleaned_dataset.parquet --output results/stats/model_results.json --figs results/figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/modeling.py", line 27, in <module>
    from setup_logging import get_model_diagnostics_logger
ImportError: cannot import name 'get_model_diagnostics_logger' from 'setup_logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/setup_logging.py)

- python code/robustness.py --input data/processed/cleaned_dataset.parquet --output results/stats/sensitivity_analysis.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/robustness.py", line 29, in <module>
    from modeling import fit_lmm, run_primary_modeling
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/modeling.py", line 27, in <module>
    from setup_logging import get_model_diagnostics_logger
ImportError: cannot import name 'get_model_diagnostics_logger' from 'setup_logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/setup_logging.py)


## Declared deliverables still missing

- data/processed/merged_dataset.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/derive_demographics.py` — NOT invoked by the run-book
    - `code/fetch_urban_rural.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
    - `code/interpolation.py` — NOT invoked by the run-book
    - `code/log_match_count.py` — NOT invoked by the run-book
    - `code/modeling.py` — IS a run-book command
    - `code/robustness.py` — IS a run-book command
    - `code/run_merge_era5_moral.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
