# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/analysis/stats.py --output results/analysis_results.csv; python src/analysis/visualize.py --input results/analysis_results.csv; 3 command(s) failed: python src/data/download.py --check-only (rc=1); python src/analysis/connectivity.py --subjects 50 (rc=1); python -m pytest tests/ -v (rc=4)

## Failing / missing run-book commands

- python src/data/download.py --check-only -> rc=1

2026-10-18 01:31:24,364 INFO code.src.data.download: Fetching OpenNeuro file index from https://openneuro.org/api/v1/datasets/ds000233/files with params {'recursive': 'true'}
2026-10-18 01:31:24,476 ERROR code.src.data.download: Pipeline failed: Failed to retrieve file index for dataset ds000233: 404 Client Error: Not Found for url: https://openneuro.org/api/v1/datasets/ds000233/files?recursive=true

- python src/analysis/connectivity.py --subjects 50 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/src/analysis/connectivity.py", line 9, in <module>
    from nilearn import input_data
ImportError: cannot import name 'input_data' from 'nilearn' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-232-investigating-the-relationship-between-b/lib/python3.11/site-packages/nilearn/__init__.py)

- python src/analysis/stats.py --output results/analysis_results.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-232-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/src/analysis/stats.py': [Errno 2] No such file or directory

- python src/analysis/visualize.py --input results/analysis_results.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-232-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/src/analysis/visualize.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=4

ERROR: /home/runner/work/llmXive/llmXive/projects/PROJ-232-investigating-the-relationship-between-b/pyproject.toml: Cannot overwrite a value (at line 96, column 25)


