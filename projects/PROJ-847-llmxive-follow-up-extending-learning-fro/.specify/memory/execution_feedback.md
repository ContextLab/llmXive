# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/control_shuffle.json`
  - script usage: `run_experiments.py [-h] [--config CONFIG] [--mode {fixed,adaptive}]`
  - argparse error: `run_experiments.py: error: argument --mode: invalid choice: 'control_shuffle' (choose from 'fixed', 'adaptive')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.llmxive.data --download (rc=1); python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json (rc=1); python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/adaptive_run.json (rc=1)

## Failing / missing run-book commands

- python -m src.llmxive.data --download -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/data.py", line 9, in <module>
    from code.data import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 25, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json -> rc=1

2026-10-18 00:18:29,262 ERROR code.run_experiments: Failed to import training utilities: No module named 'torch'

- python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/adaptive_run.json -> rc=1

2026-10-18 00:18:29,333 ERROR code.run_experiments: Adaptive mode not yet implemented in this task.

- python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/control_shuffle.json -> rc=2

usage: run_experiments.py [-h] [--config CONFIG] [--mode {fixed,adaptive}]
                          [--rhos RHOS [RHOS ...]] [--seeds SEEDS [SEEDS ...]]
                          [--output OUTPUT] [--dry-run]
run_experiments.py: error: argument --mode: invalid choice: 'control_shuffle' (choose from 'fixed', 'adaptive')

- python -m src.llmxive.analysis  --fixed outputs/fixed_baselines.json  --adaptive outputs/adaptive_run.json  --control outputs/control_shuffle.json  --outdir outputs/statistics -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/analysis.py", line 10, in <module>
    from code.analysis import *  # noqa: F403,F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'code.analysis'

