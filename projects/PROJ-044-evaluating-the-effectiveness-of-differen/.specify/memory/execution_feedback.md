# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/partition.py  --seed-list 42,43,44,45,46  --alphas 0.1,0.5,1.0  --clients 100`
  - script usage: `partition.py [-h] --data DATA [--output OUTPUT]`
  - argparse error: `partition.py: error: argument --alphas: invalid float value: '0.1,0.5,1.0'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/data/verify_checksum.py data/raw/femnist.parquet data/raw/femnist.sha256; python code/main.py sweep  --dataset femnist  --alphas 0.1,0.5,1.0  --epsilons 0.1,0.5,1.0,5.0,inf  --seeds 42,43,44,45,46; 6 command(s) failed: python code/data/download.py --dataset femnist (rc=1); python code/data/partition.py  --seed-list 42,43,44,45,46  --alphas 0.1,0.5,1.0  --clients 100 (rc=2); python code/analysis/stats.py  --input results/raw_logs.csv (rc=1); 1 declared deliverable(s) absent: data/raw/femnist.parquet

## Failing / missing run-book commands

- python code/data/download.py --dataset femnist -> rc=1

2026-10-13 09:51:03,548 - __main__ - INFO - Starting download for dataset: femnist
2026-10-13 09:51:03,548 - __main__ - INFO - Starting streaming download of leaf/femnist...
2026-10-13 09:51:03,600 - __main__ - ERROR - Data Fetch Error: Hugging Face 'datasets' library is not installed. Please install it via requirements.txt.

- python code/data/verify_checksum.py data/raw/femnist.parquet data/raw/femnist.sha256 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/data/verify_checksum.py': [Errno 2] No such file or directory

- python code/data/partition.py  --seed-list 42,43,44,45,46  --alphas 0.1,0.5,1.0  --clients 100 -> rc=2

usage: partition.py [-h] --data DATA [--output OUTPUT]
                    [--seeds SEEDS [SEEDS ...]] [--alphas ALPHAS [ALPHAS ...]]
partition.py: error: argument --alphas: invalid float value: '0.1,0.5,1.0'

- python code/main.py sweep  --dataset femnist  --alphas 0.1,0.5,1.0  --epsilons 0.1,0.5,1.0,5.0,inf  --seeds 42,43,44,45,46 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/main.py': [Errno 2] No such file or directory

- python code/analysis/stats.py  --input results/raw_logs.csv -> rc=1
ed_data.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 469, in <module>
    results = run_experiment_analysis(args.input, args.output, args.p_values)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 375, in run_experiment_analysis
    filtered_df = load_filtered_data(input_time_filtered, output_filtered)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 344, in load_filtered_data
    df = load_metrics_from_csv(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 23, in load_metrics_from_csv
    raise FileNotFoundError(f"Metrics file not found: {file_path}")
FileNotFoundError: Metrics file not found: results/raw_logs.csv

- python code/analysis/stats.py  --input results/filtered_data.csv  --output results/final_stats.csv -> rc=1
ts.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 469, in <module>
    results = run_experiment_analysis(args.input, args.output, args.p_values)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 375, in run_experiment_analysis
    filtered_df = load_filtered_data(input_time_filtered, output_filtered)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 344, in load_filtered_data
    df = load_metrics_from_csv(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py", line 23, in load_metrics_from_csv
    raise FileNotFoundError(f"Metrics file not found: {file_path}")
FileNotFoundError: Metrics file not found: results/filtered_data.csv

- python code/analysis/plots.py  --stats results/final_stats.csv  --output-dir figures/ -> rc=1

2026-10-13 09:51:06,316 - __main__ - ERROR - Data file not found: results/filtered_data.csv
2026-10-13 09:51:06,316 - __main__ - ERROR - Please run T035 (filter_utility_collapse) first to generate results/filtered_data.csv

- python code/analysis/generate_summary.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/generate_summary.py", line 26, in <module>
    from code.analysis.stats import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/__init__.py", line 8, in <module>
    from .stats import (
ImportError: cannot import name 'calculate_summary_statistics' from 'code.analysis.stats' (/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py)


## Declared deliverables still missing

- data/raw/femnist.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/femnist.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregation.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/__init__.py` — NOT invoked by the run-book
    - `code/data/download.py` — IS a run-book command
    - `code/data/generate_partition_metadata.py` — NOT invoked by the run-book
    - `code/data/partition.py` — IS a run-book command
    - `code/training/fedavg.py` — NOT invoked by the run-book
    - `code/training/logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/femnist.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
