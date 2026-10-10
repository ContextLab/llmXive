# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; python code/validate.py --input data/results/fork_points/ --output data/results/validation/; python code/report.py --input data/results/validation/ --output data/results/report/; 3 command(s) failed: python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852 (rc=1); python code/preprocess.py --input data/raw/ --output data/processed/ (rc=1); python code/velocity.py --input data/processed/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852 -> rc=1
Verifying SRA Toolkit installation...
✗ 'prefetch' command not found in PATH.
  Please ensure SRA Toolkit is installed and added to PATH.
2026-10-10 15:13:40,674 - ERROR - SRA Toolkit not found or non-functional. Please run install_sra_toolkit.py first.


- python code/preprocess.py --input data/raw/ --output data/processed/ -> rc=1
2026-10-10 15:13:42,934 - INFO - Checking R environment...
2026-10-10 15:13:42,935 - ERROR - R executable not found in PATH.
2026-10-10 15:13:42,935 - ERROR - No dataset directories found in data/raw


- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/velocity.py", line 17, in <module>
    import scvelo as scv
ModuleNotFoundError: No module named 'scvelo'

- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/validate.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory

