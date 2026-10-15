# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/ (rc=1); python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2 (rc=1); python -m pytest -v tests/ (rc=1); 4 declared deliverable(s) absent: data/derived/clean_subjects.parquet; data/derived/invalid_parcels.csv; data/derived/subject_qc.csv

## Failing / missing run-book commands

- python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/ -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/download_data.py", line 16, in <module>
    from src.data.download_hcp import main as download_hcp_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/data/download_hcp.py", line 19, in <module>
    from nilearn.input_data import NiftiLabelsMasker
ModuleNotFoundError: No module named 'nilearn.input_data'

- python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/compute_entropy.py", line 19, in <module>
    from src.analysis.entropy import multiscale_entropy
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/src/analysis/entropy.py", line 29, in <module>
    from pyentropy import sample_entropy
ModuleNotFoundError: No module named 'pyentropy'

- python -m pytest -v tests/ -> rc=1
it/test_data_download.py::TestHCPCredentialValidation::test_validate_hcp_credentials_whitespace_token
FAILED tests/unit/test_data_download.py::TestHCPCredentialValidation::test_environment_error_type
FAILED tests/unit/test_env_manager.py::TestGetHcpToken::test_hcp_token_missing
FAILED tests/unit/test_env_manager.py::TestGetHcpToken::test_hcp_token_empty
FAILED tests/unit/test_env_manager.py::TestGetHcpToken::test_hcp_token_whitespace_only
FAILED tests/unit/test_env_manager.py::TestValidateHcpCredentials::test_invalid_credentials
FAILED tests/unit/test_env_manager.py::TestValidateHcpCredentials::test_token_too_short
FAILED tests/unit/test_env_manager.py::TestCheckEnvironment::test_all_good - ...
FAILED tests/unit/test_env_manager.py::TestCheckEnvironment::test_missing_token
FAILED tests/unit/test_env_manager.py::TestMain::test_main_success - Failed: ...
FAILED tests/unit/test_env_manager.py::TestMain::test_main_failure - Assertio...
FAILED tests/unit/test_lint_format.py::TestLintFormatConfig::test_pyproject_config_exists
FAILED tests/unit/test_lint_format.py::TestLintFormatConfig::test_ruff_check_runs
======================== 15 failed, 18 passed in 0.63s =========================



## Declared deliverables still missing

- data/derived/clean_subjects.parquet
- data/derived/invalid_parcels.csv
- data/derived/subject_qc.csv
- data/raw/dsrt_scores.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/clean_subjects.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/run_pipeline.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/clean_subjects.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
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
