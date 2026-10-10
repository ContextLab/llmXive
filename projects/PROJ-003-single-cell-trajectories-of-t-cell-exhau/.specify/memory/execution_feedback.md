# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; python code/validate.py --input data/results/fork_points/ --output data/results/validation/; python code/report.py --input data/results/validation/ --output data/results/report/; 3 command(s) failed: python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852 (rc=1); python code/preprocess.py --input data/raw/ --output data/processed/ (rc=1); python code/velocity.py --input data/processed/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852 -> rc=1
s/GSE138nnn/GSE138852/suppl/GSE138852_counts.csv.gz → /home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/data/raw/GSE138852/counts/GSE138852_counts.csv.gz
2026-10-10 14:14:51,916 - INFO - Downloading https://ftp.ncbi.nlm.nih.gov/geo/series/GSE138nnn/GSE138852/suppl/GSE138852_covariates.csv.gz → /home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/data/raw/GSE138852/counts/GSE138852_covariates.csv.gz
2026-10-10 14:14:51,953 - INFO - Downloading https://ftp.ncbi.nlm.nih.gov/geo/series/GSE138nnn/GSE138852/suppl/https://www.hhs.gov/vulnerability-disclosure-policy/index.html → /home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/data/raw/GSE138852/counts/https:/www.hhs.gov/vulnerability-disclosure-policy/index.html
2026-10-10 14:14:51,982 - ERROR - Failed to process GSE138852: HTTP error while downloading https://ftp.ncbi.nlm.nih.gov/geo/series/GSE138nnn/GSE138852/suppl/https://www.hhs.gov/vulnerability-disclosure-policy/index.html: HTTP Error 404: Not Found
2026-10-10 14:14:51,987 - CRITICAL - Data preparation failed for: GSE136103, GSE127465, GSE111075, GSE138852


- python code/preprocess.py --input data/raw/ --output data/processed/ -> rc=1
2026-10-10 14:14:54,778 - INFO - Checking R environment...
2026-10-10 14:14:54,779 - ERROR - R executable not found in PATH.
2026-10-10 14:14:54,779 - INFO - Running Python fallback preprocessing for data/raw
2026-10-10 14:14:54,781 - INFO - Detected input file data/raw/GSE127465/counts/GSE127465_human_counts_normalized_54773x41861.mtx.gz
2026-10-10 14:15:06,455 - WARNING - No mitochondrial genes detected; setting percent.mt to 0 for all cells.
2026-10-10 14:15:06,665 - INFO - Cells before QC: 41861, after QC (<=20% mito): 41861
2026-10-10 14:15:10,952 - ERROR - Failed to write .h5ad file: [Errno 21] Unable to synchronously create file (unable to open file: name = 'data/processed', errno = 21, error message = 'Is a directory', flags = 13, o_flags = 242)
2026-10-10 14:15:10,954 - ERROR - Both R and Python preprocessing failed.

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/lib/python3.11/site-packages/legacy_api_wrap/__init__.py:88: UserWarning: Some cells have zero counts
  return fn(*args_all, **kw)

- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=1
2026-10-10 14:15:13,340 - ERROR - Input file not found: data/processed


- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/validate.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory

