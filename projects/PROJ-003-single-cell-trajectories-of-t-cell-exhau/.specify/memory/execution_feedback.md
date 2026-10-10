# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; python code/validate.py --input data/results/fork_points/ --output data/results/validation/; python code/report.py --input data/results/validation/ --output data/results/report/; 3 command(s) failed: python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852 (rc=1); python code/preprocess.py --input data/raw/ --output data/processed/ (rc=1); python code/velocity.py --input data/processed/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852 -> rc=1
16:32,617 - ERROR - Failed to process GSE111075: Failed to install SRA Toolkit via conda.
2026-10-10 12:16:32,624 - INFO - Processing GSE138852 …
Installing SRA Toolkit via conda...
Found conda executable: conda
Running: conda install -y -c bioconda -c conda-forge sratoolkit
✗ Failed to install SRA Toolkit via conda.
  Stderr: 
CondaToSNonInteractiveError: Terms of Service have not been accepted for the following channels. Please accept or remove them before proceeding:
    - https://repo.anaconda.com/pkgs/main
    - https://repo.anaconda.com/pkgs/r

To accept these channels' Terms of Service, run the following commands:
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

For information on safely removing channels from your conda configuration,
please see the official documentation:

    https://www.anaconda.com/docs/tools/working-with-conda/channels


2026-10-10 12:16:33,703 - ERROR - Failed to process GSE138852: Failed to install SRA Toolkit via conda.
2026-10-10 12:16:33,709 - CRITICAL - Data preparation failed for: GSE136103, GSE127465, GSE111075, GSE138852


- python code/preprocess.py --input data/raw/ --output data/processed/ -> rc=1
2026-10-10 12:16:36,276 - INFO - Checking R environment...
2026-10-10 12:16:36,276 - ERROR - R executable not found in PATH.
2026-10-10 12:16:36,276 - INFO - Running Python fallback preprocessing for data/raw
2026-10-10 12:16:36,277 - ERROR - No supported matrix files found in directory data/raw
2026-10-10 12:16:36,277 - ERROR - Both R and Python preprocessing failed.


- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=1
2026-10-10 12:16:38,555 - ERROR - Input file not found: data/processed


- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/validate.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory

