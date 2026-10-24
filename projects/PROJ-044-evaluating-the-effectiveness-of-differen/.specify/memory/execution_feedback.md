# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/partition.py  --train data/raw/femnist_train.parquet  --test  data/raw/femnist_test.parquet  --output data/partitions  --seeds 42 43 44 45 46 47 48 49 50 51  --alphas 0.1 0.5 1.0`
  - script usage: `partition.py [-h] --data DATA [--output OUTPUT]`
  - argparse error: `partition.py: error: the following arguments are required: --data`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py --dataset femnist`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data/download.py --dataset femnist (rc=1); python -c " (rc=-1); python code/data/partition.py  --train data/raw/femnist_train.parquet  --test  data/raw/femnist_test.parquet  --output data/partitions  --seeds 42 43 44 45 46 47 48 49 50 51  --alphas 0.1 0.5 1.0 (rc=2)

## Failing / missing run-book commands

- python code/data/download.py --dataset femnist -> rc=1
_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/lib/python3.11/site-packages/datasets/load.py", line 1904, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-044-evaluating-the-effectiveness-of-differen/lib/python3.11/site-packages/datasets/load.py", line 1850, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'federated/femnist' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/federated/femnist to ask for access.
2026-10-24 17:37:25,401 ERROR __main__: Data fetch error: Failed to load FEMNIST train split: Dataset 'federated/femnist' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/federated/femnist to ask for access.

- python -c " -> rc=-1
unparseable command (shlex)
- python code/data/partition.py  --train data/raw/femnist_train.parquet  --test  data/raw/femnist_test.parquet  --output data/partitions  --seeds 42 43 44 45 46 47 48 49 50 51  --alphas 0.1 0.5 1.0 -> rc=2

usage: partition.py [-h] --data DATA [--output OUTPUT]
                    [--seeds SEEDS [SEEDS ...]] [--alphas ALPHAS [ALPHAS ...]]
partition.py: error: the following arguments are required: --data

- python code/analysis/stats.py  --input results/raw_logs.csv  --output results/final_stats.csv -> rc=1
l_stats.csv
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

- python code/analysis/plots.py -> rc=1

2026-10-24 17:37:27,187 - __main__ - ERROR - Data file not found: results/filtered_data.csv
2026-10-24 17:37:27,187 - __main__ - ERROR - Please run T035 (filter_utility_collapse) first to generate results/filtered_data.csv

- python code/analysis/generate_summary.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/generate_summary.py", line 26, in <module>
    from code.analysis.stats import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/__init__.py", line 8, in <module>
    from .stats import (
ImportError: cannot import name 'calculate_summary_statistics' from 'code.analysis.stats' (/home/runner/work/llmXive/llmXive/projects/PROJ-044-evaluating-the-effectiveness-of-differen/code/analysis/stats.py)

