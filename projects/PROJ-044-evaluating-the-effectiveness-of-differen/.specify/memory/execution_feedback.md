# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py sweep  --dataset femnist  --alphas 0.1,0.5,1.0  --epsilons 0.1,0.5,1.0,5.0,inf  --seeds 42,43,44,45,46; 7 command(s) failed: python code/setup_check.py (rc=1); python code/data/download.py --dataset femnist (rc=1); python code/data/partition.py  --data data/raw/femnist.parquet  --output data/partitions  --seeds 42 43 44 45 46  --alphas 0.1 0.5 1.0 (rc=1); 1 declared deliverable(s) absent: data/raw/femnist.parquet

## Failing / missing run-book commands

- python code/setup_check.py -> rc=1
/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/data/raw
  DIR   data/partitions -> /home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/data/partitions

  FAIL  datasets: pyarrow requires NumPy 2.0 or newer, found 1.26.4
  FAIL  pyarrow: pyarrow requires NumPy 2.0 or newer, found 1.26.4
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/setup_check.py", line 87, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/setup_check.py", line 71, in main
    ensure_directories()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/setup_check.py", line 57, in ensure_directories
    placeholder.unlink()
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1147, in unlink
    os.unlink(self)
IsADirectoryError: [Errno 21] Is a directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/results/.placeholder'

- python code/data/download.py --dataset femnist -> rc=1

2026-10-13 09:54:28,083 - __main__ - INFO - Starting download for dataset: femnist
2026-10-13 09:54:28,083 - __main__ - INFO - Starting streaming download of leaf/femnist...
2026-10-13 09:54:28,131 - __main__ - ERROR - Data Fetch Error: Hugging Face 'datasets' library is not installed. Please install it via requirements.txt.

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

2026-10-13 09:54:28,539 - __main__ - ERROR - Data file not found: data/raw/femnist.parquet
2026-10-13 09:54:28,539 - __main__ - ERROR - Please ensure T011 (download) has completed successfully.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/data/partition.py", line 428, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/data/partition.py", line 401, in main
    raise PartitionError("Data file not found")
PartitionError: Data file not found

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

- python code/analysis/plots.py -> rc=1

2026-10-13 09:54:30,491 - __main__ - ERROR - Data file not found: results/filtered_data.csv
2026-10-13 09:54:30,491 - __main__ - ERROR - Please run T035 (filter_utility_collapse) first to generate results/filtered_data.csv

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
