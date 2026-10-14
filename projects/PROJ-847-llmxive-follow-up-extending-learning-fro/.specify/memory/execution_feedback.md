# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv`
  - script usage: `python -m code.run_experiments [-h] [--config CONFIG]`
  - argparse error: `python -m code.run_experiments: error: unrecognized arguments: --mode fixed --rhos 0.1 0.3 0.5 0.7 0.9 --seeds 42 43 44 --output outputs/fixed_baselines.csv`
- run-book command: `python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json`
  - script usage: `python -m code.run_experiments [-h] [--config CONFIG]`
  - argparse error: `python -m code.run_experiments: error: unrecognized arguments: --mode adaptive --seeds 42 43 44 --output outputs/adaptive_run.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data.py --download (rc=1); python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv (rc=2); python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json (rc=2)

## Failing / missing run-book commands

- python code/data.py --download -> rc=1
/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 252, in main
    download_all()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 199, in download_all
    n_gsm = _snapshot_to_jsonl(
            ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 175, in _snapshot_to_jsonl
    for row in iterable:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 101, in _fetch_parquet
    raise RuntimeError(
RuntimeError: Failed to parse Parquet file for openai/gsm8k/main/test: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv -> rc=2

usage: python -m code.run_experiments [-h] [--config CONFIG]
                                      [--stage {adaptive_runs,analysis,data,fixed_baselines,model}]
                                      [--seed SEED] [--dry-run]
python -m code.run_experiments: error: unrecognized arguments: --mode fixed --rhos 0.1 0.3 0.5 0.7 0.9 --seeds 42 43 44 --output outputs/fixed_baselines.csv

- python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json -> rc=2

usage: python -m code.run_experiments [-h] [--config CONFIG]
                                      [--stage {adaptive_runs,analysis,data,fixed_baselines,model}]
                                      [--seed SEED] [--dry-run]
python -m code.run_experiments: error: unrecognized arguments: --mode adaptive --seeds 42 43 44 --output outputs/adaptive_run.json

- python -m code.analysis  --fixed outputs/fixed_baselines.csv  --adaptive outputs/adaptive_run.json  --outdir outputs/statistics -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: No module named code.analysis

