# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json (rc=1); python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet (rc=1); python code/preprocessing.py --input data/processed/merged_dataset.parquet --output data/processed/cleaned_dataset.parquet (rc=1); 1 declared deliverable(s) absent: data/processed/merged_dataset.parquet

## Failing / missing run-book commands

- python code/validate_sources.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output results/logs/validation_report.json -> rc=1
2026-10-13 19:25:44,863 - data_quality - ERROR - File not found: data/raw/moral_machine.csv
2026-10-13 19:25:44,863 - data_quality - INFO - Validation report written to results/logs/validation_report.json


- python code/ingestion.py --input data/raw/moral_machine.csv --temp data/raw/era5_data/ --output data/processed/merged_dataset.parquet -> rc=1
2026-10-13 19:25:45,266 - ingestion - INFO - Starting ingestion pipeline
2026-10-13 19:25:45,266 - ingestion - INFO - Input: --input
2026-10-13 19:25:45,266 - ingestion - INFO - Output: --temp
2026-10-13 19:25:45,266 - ingestion - INFO - Loading Moral Machine data from --input
2026-10-13 19:25:45,266 - ingestion - ERROR - Ingestion pipeline failed: Input file not found: --input
2026-10-13 19:25:45,266 - data_quality - ERROR - Ingestion pipeline failed: Input file not found: --input

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
2026-10-13 19:25:45,646 - preprocessing - INFO - Starting T033d: Compute Temperature-Adjusted Response Times
2026-10-13 19:25:45,646 - preprocessing - INFO - Input: data/processed/merged_dataset.parquet
2026-10-13 19:25:45,646 - preprocessing - INFO - Output: data/processed/cleaned_dataset.parquet
2026-10-13 19:25:45,656 - preprocessing - ERROR - Failed to load input dataset: [Errno 2] No such file or directory: 'data/processed/merged_dataset.parquet'


- python code/modeling.py --input data/processed/cleaned_dataset.parquet --output results/stats/model_results.json --figs results/figures/ -> rc=1
2026-10-13 19:25:46,598 - model_diagnostics - INFO - Starting T025: Modeling (Log-transform & Convergence Fallback)
2026-10-13 19:25:46,598 - model_diagnostics - CRITICAL - Modeling pipeline failed: Required merged dataset not found at data/processed/merged_dataset.parquet. Please ensure T022 (output generation) has been executed successfully.


- python code/robustness.py --input data/processed/cleaned_dataset.parquet --output results/stats/sensitivity_analysis.csv -> rc=1
2026-10-13 19:25:47,602 - __main__ - INFO - Loading data from data/processed/cleaned_dataset.parquet
2026-10-13 19:25:47,602 - __main__ - ERROR - Bootstrap analysis failed: Input file not found: data/processed/cleaned_dataset.parquet

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/robustness.py", line 268, in main
    df = load_data(args.input)
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-743-ambient-temperature-influence-on-moral-d/code/robustness.py", line 61, in load_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/processed/cleaned_dataset.parquet


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
