# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 (rc=1); python -m pytest -v tests/ (rc=-1); 5 declared deliverable(s) absent: data/derived/clean_subjects.parquet; data/derived/entropy_matrix.parquet; data/derived/invalid_parcels.csv

## Failing / missing run-book commands

- python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 -> rc=1
_run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/src/run_pipeline.py", line 14, in <module>
    from code.src.run_pipeline import main as _real_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/__init__.py", line 11, in <module>
    from . import run_pipeline as run_pipeline  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/run_pipeline.py", line 15, in <module>
    from code.src.pipeline import run_pipeline as orchestrator
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/pipeline.py", line 20, in <module>
    from code.src.compute_entropy import main as entropy_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/compute_entropy.py", line 19, in <module>
    from src.analysis.entropy import multiscale_entropy
ModuleNotFoundError: No module named 'src.analysis'

- python -m pytest -v tests/ -> rc=-1
tials PASSED [ 39%]
tests/unit/test_env_manager.py::TestValidateHcpCredentials::test_token_too_short PASSED [ 42%]
tests/unit/test_env_manager.py::TestGetOptionalEnv::test_env_present PASSED [ 45%]
tests/unit/test_env_manager.py::TestGetOptionalEnv::test_env_missing_with_default PASSED [ 48%]
tests/unit/test_env_manager.py::TestGetOptionalEnv::test_env_missing_no_default PASSED [ 51%]
tests/unit/test_env_manager.py::TestCheckEnvironment::test_all_good PASSED [ 54%]
tests/unit/test_env_manager.py::TestCheckEnvironment::test_missing_token FAILED [ 57%]
tests/unit/test_env_manager.py::TestMain::test_main_success PASSED       [ 60%]
tests/unit/test_env_manager.py::TestMain::test_main_failure PASSED       [ 63%]
tests/unit/test_lint_format.py::TestLintFormatConfig::test_ruff_config_exists PASSED [ 66%]
tests/unit/test_lint_format.py::TestLintFormatConfig::test_pyproject_config_exists FAILED [ 69%]
tests/unit/test_lint_format.py::TestLintFormatConfig::test_lint_format_script_syntax PASSED [ 72%]
tests/unit/test_lint_format.py::TestLintFormatConfig::test_lint_format_help_command PASSED [ 75%]
tests/unit/test_lint_format.py::TestLintFormatConfig::test_ruff_check_runs 

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/derived/clean_subjects.parquet
- data/derived/entropy_matrix.parquet
- data/derived/invalid_parcels.csv
- data/derived/subject_qc.csv
- data/raw/dsrt_scores.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/clean_subjects.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/clean_subjects.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/entropy_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/entropy_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/invalid_parcels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/tests/unit/test_entropy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/invalid_parcels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/subject_qc.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/subject_qc.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dsrt_scores.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download_hcp.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dsrt_scores.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
