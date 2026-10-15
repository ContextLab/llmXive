# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/`
  - script usage: `download_data.py [-h] [--subject-limit SUBJECT_LIMIT]`
  - argparse error: `download_data.py: error: unrecognized arguments: --hcp-token $HCP_TOKEN --fd-threshold 0.2`
- run-book command: `python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2`
  - script usage: `compute_entropy.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `compute_entropy.py: error: unrecognized arguments: --average`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/ (rc=2); python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2 (rc=2); python -m pytest -v tests/ (rc=-1); 4 declared deliverable(s) absent: data/derived/clean_subjects.parquet; data/derived/invalid_parcels.csv; data/derived/subject_qc.csv

## Failing / missing run-book commands

- python -m src.download_data  --hcp-token $HCP_TOKEN  --subject-limit 200  --fd-threshold 0.2  --output-dir data/ -> rc=2

usage: download_data.py [-h] [--subject-limit SUBJECT_LIMIT]
                        [--output-dir OUTPUT_DIR]
download_data.py: error: unrecognized arguments: --hcp-token $HCP_TOKEN --fd-threshold 0.2

- python -m src.compute_entropy  --input data/derived/clean_subjects.parquet  --output data/derived/entropy_matrix.parquet  --scales 1 2 3 4 5  --average  --r 0.15  --m 2 -> rc=2

usage: compute_entropy.py [-h] --input INPUT --output OUTPUT
                          [--scales SCALES [SCALES ...]] [--m M] [--r R]
                          [--batch-size BATCH_SIZE]
compute_entropy.py: error: unrecognized arguments: --average

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
