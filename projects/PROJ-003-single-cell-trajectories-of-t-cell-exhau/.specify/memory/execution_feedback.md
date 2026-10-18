# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/download_data.py  --datasets GSE136103 GSE127465 GSE111075 GSE138852  --output data/raw/`
  - script usage: `download_data.py [-h] [--datasets DATASETS]`
  - argparse error: `download_data.py: error: unrecognized arguments: GSE127465 GSE111075 GSE138852 --output data/raw/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python code/subset_tcells.py --input data/processed/ --output data/processed/; python code/batch_correct.py --input data/processed/ --output data/processed/; python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; 3 command(s) failed: python code/download_data.py  --datasets GSE136103 GSE127465 GSE111075 GSE138852  --output data/raw/ (rc=2); python code/preprocess.py --input data/raw/ --output data/processed/ (rc=1); python code/velocity.py --input data/processed/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/download_data.py  --datasets GSE136103 GSE127465 GSE111075 GSE138852  --output data/raw/ -> rc=2

usage: download_data.py [-h] [--datasets DATASETS]
download_data.py: error: unrecognized arguments: GSE127465 GSE111075 GSE138852 --output data/raw/

- python code/preprocess.py --input data/raw/ --output data/processed/ -> rc=1
2026-10-18 09:36:47,170 - INFO - Checking R environment...
2026-10-18 09:36:47,170 - ERROR - R executable not found in PATH.
2026-10-18 09:36:47,170 - ERROR - No dataset directories found in data/raw


- python code/subset_tcells.py --input data/processed/ --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/subset_tcells.py': [Errno 2] No such file or directory

- python code/batch_correct.py --input data/processed/ --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/batch_correct.py': [Errno 2] No such file or directory

- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/velocity.py", line 18, in <module>
    import scvelo as scv
ModuleNotFoundError: No module named 'scvelo'

- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/power_analysis.py --input data/processed/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/power_analysis.py': [Errno 2] No such file or directory

- python code/enrichment.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/enrichment.py': [Errno 2] No such file or directory

- python code/validate.py   --input data/results/validation/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-003-single-cell-trajectories-of-t-cell-exhau/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory

