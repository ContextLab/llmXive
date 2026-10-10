# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; python code/validate.py --input data/results/fork_points/ --output data/results/validation/; python code/report.py --input data/results/validation/ --output data/results/report/; 1 command(s) failed: python code/velocity.py --input data/processed/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=1
2026-10-10 14:25:13,252 - ERROR - Directory data/processed does not contain GSE136103_processed.h5ad


- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/validate.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory

