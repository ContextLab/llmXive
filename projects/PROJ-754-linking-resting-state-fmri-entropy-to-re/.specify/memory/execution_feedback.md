# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/ (rc=1); python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2 (rc=1); python -m src.run_stats  --entropy data/derived/entropy_matrix.parquet  --covariates data/derived/clean_subjects.parquet  --n-permutations 5000  --max-runtime 10800  --output-dir results/ (rc=1); 1 declared deliverable(s) absent: data/raw/dsrt_scores.parquet

## Failing / missing run-book commands

- python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/bin/python: No module named src.download_data

- python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/bin/python: No module named src.compute_entropy

- python -m src.run_stats  --entropy data/derived/entropy_matrix.parquet  --covariates data/derived/clean_subjects.parquet  --n-permutations 5000  --max-runtime 10800  --output-dir results/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/bin/python: No module named src.run_stats

- python -m src.generate_report  --coeffs results/model_coefficients.csv  --nii results/significant_parcels.nii.gz  --sensitivity data/derived/sensitivity.parquet  --power-output results/power_analysis.csv  --output reports/link_entropy_risk.pdf -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/bin/python: No module named src.generate_report

- python -m pytest -v tests/ -> rc=2
ate-fmri-entropy-to-re/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re
configfile: pyproject.toml
plugins: platformdirs-4.13.0
collecting ... collected 18 items / 1 error

==================================== ERRORS ====================================
_______________ ERROR collecting tests/unit/test_env_manager.py ________________
tests/unit/test_env_manager.py:12: in <module>
    from config.env_manager import (
code/config/__init__.py:2: in <module>
    from .lint_format import run_command, check_ruff_installed, check_black_installed, run_lint_check, run_format_check, run_lint_fix, run_format_fix, main as lint_main
code/config/lint_format.py:6: in <module>
    def run_command(cmd: list[str], cwd: Optional[Path] = None) -> int:
E   NameError: name 'Optional' is not defined
=========================== short test summary info ============================
ERROR tests/unit/test_env_manager.py - NameError: name 'Optional' is not defined
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.36s ===============================



## Declared deliverables still missing

- data/raw/dsrt_scores.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dsrt_scores.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download_hcp.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dsrt_scores.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
