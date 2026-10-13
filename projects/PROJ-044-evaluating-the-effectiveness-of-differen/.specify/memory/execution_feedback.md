# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data/download.py --dataset femnist (rc=1); python code/data/partition.py  --data data/raw/femnist.parquet  --output data/partitions  --seeds 42 43 44 45 46  --alphas 0.1 0.5 1.0 (rc=1); python code/analysis/stats.py  --input results/raw_logs.csv (rc=1); 1 declared deliverable(s) absent: data/raw/femnist.parquet

## Failing / missing run-book commands

- python code/data/download.py --dataset femnist -> rc=1
, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -c "import hashlib, pathlib; p = pathlib.Path('data/raw/femnist.parquet'); expected = pathlib.Path('data/raw/femnist.sha256').read_text().split()[0]; actual = hashlib.sha256(p.read_bytes()).hexdigest(); assert actual == expected, 'checksum mismatch'; print('checksum OK:', actual)" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1058, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/femnist.sha256'

- python code/data/partition.py  --data data/raw/femnist.parquet  --output data/partitions  --seeds 42 43 44 45 46  --alphas 0.1 0.5 1.0 -> rc=1

2026-10-13 14:18:01,772 - __main__ - ERROR - Data file not found: data/raw/femnist.parquet
2026-10-13 14:18:01,772 - __main__ - ERROR - Please ensure T011 (download) has completed successfully.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/data/partition.py", line 428, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/data/partition.py", line 401, in main
    raise PartitionError("Data file not found")
PartitionError: Data file not found

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

- python code/analysis/plots.py -> rc=1

2026-10-13 14:18:03,992 - __main__ - ERROR - Data file not found: results/filtered_data.csv
2026-10-13 14:18:03,992 - __main__ - ERROR - Please run T035 (filter_utility_collapse) first to generate results/filtered_data.csv

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
    - `code/main.py` — IS a run-book command
    - `code/training/fedavg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/femnist.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
