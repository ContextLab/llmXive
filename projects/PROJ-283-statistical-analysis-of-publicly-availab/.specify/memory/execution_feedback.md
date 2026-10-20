# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/validation/validate_contracts.py --input data/processed/sample_games.csv --schema contracts/game_record.schema.yaml`
  - script usage: `validate_contracts.py [-h] --data DATA [--contracts CONTRACTS]`
  - argparse error: `validate_contracts.py: error: the following arguments are required: --data`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python src/data/download.py --verify-only (rc=1); python src/data/download.py --sample-size 100 --output data/raw/sample.parquet (rc=1); python src/validation/validate_contracts.py --input data/processed/sample_games.csv --schema contracts/game_record.schema.yaml (rc=2); 7 declared deliverable(s) absent: data/processed/games.parquet; data/results/cv_metrics.json; data/results/dataset_verification.json

## Failing / missing run-book commands

- python src/data/download.py --verify-only -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/data/download.py", line 10, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/data/download.py --sample-size 100 --output data/raw/sample.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/data/download.py", line 10, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/validation/validate_contracts.py --input data/processed/sample_games.csv --schema contracts/game_record.schema.yaml -> rc=2

usage: validate_contracts.py [-h] --data DATA [--contracts CONTRACTS]
                             [--format {parquet,csv}]
validate_contracts.py: error: the following arguments are required: --data

- python src/main.py --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/main.py", line 23, in <module>
    from src.data.download import download_lichess_data
ImportError: cannot import name 'download_lichess_data' from 'src.data.download' (/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/code/src/data/download.py)

- python -m pytest tests/contract -v -> rc=2
availab/src/validation/validate_contracts.py)
______________ ERROR collecting tests/contract/test_validation.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/tests/contract/test_validation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_validation.py:8: in <module>
    from src.validation.validate_contracts import (
E   ImportError: cannot import name 'ValidationResult' from 'src.validation.validate_contracts' (/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/validation/validate_contracts.py)
=========================== short test summary info ============================
ERROR tests/contract/test_validate_contracts.py
ERROR tests/contract/test_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.27s ===============================


- python -m pytest tests/unit -v -> rc=2
cache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_sensitivity_edge_cases.py:4: in <module>
    from src.reports.sensitivity import calculate_jaccard_index, get_significant_predictors, perform_threshold_sweep
E   ImportError: cannot import name 'calculate_jaccard_index' from 'src.reports.sensitivity' (/home/runner/work/llmXive/llmXive/projects/PROJ-283-statistical-analysis-of-publicly-availab/src/reports/sensitivity.py)
=========================== short test summary info ============================
ERROR tests/unit/test_calculations.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_material_imbalance_edge_cases.py
ERROR tests/unit/test_metrics_edge_cases.py
ERROR tests/unit/test_parsers.py
ERROR tests/unit/test_parsers_malformed_data.py
ERROR tests/unit/test_process_edge_cases.py
ERROR tests/unit/test_save_metrics.py
ERROR tests/unit/test_sensitivity.py
ERROR tests/unit/test_sensitivity_edge_cases.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 0.87s ==============================


- python -m pytest tests/integration -v -> rc=2
gcd_import(name[level:], package, level)
tests/integration/test_pipeline.py:15: in <module>
    from src.data.download import download_lichess_games
src/data/download.py:10: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py:17: in <module>
    from .arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-283-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.43s ===============================



## Declared deliverables still missing

- data/processed/games.parquet
- data/results/cv_metrics.json
- data/results/dataset_verification.json
- data/results/diagnostics.json
- data/results/inclusion_metrics.json
- data/results/model_metrics.json
- data/results/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/games.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/src/config.py` — NOT invoked by the run-book
    - `code/src/data/download.py` — NOT invoked by the run-book
    - `code/src/data/parse.py` — NOT invoked by the run-book
    - `code/src/data/process.py` — NOT invoked by the run-book
    - `code/src/data/verify_dataset.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/models/validate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/games.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/cv_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/models/validate.py` — NOT invoked by the run-book
    - `code/src/reports/generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_validate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cv_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/dataset_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/verify_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/dataset_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/reports/generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_diagnostics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_plots.py` — NOT invoked by the run-book
    - `code/tests/unit/test_quickstart_validation.py` — NOT invoked by the run-book
    - `src/reports/generate_plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/inclusion_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/parse.py` — NOT invoked by the run-book
    - `code/src/data/process.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/tests/unit/test_process_metrics.py` — NOT invoked by the run-book
    - `src/data/process.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/inclusion_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/models/fit.py` — NOT invoked by the run-book
    - `code/src/models/save_metrics.py` — NOT invoked by the run-book
    - `code/src/models/validate.py` — NOT invoked by the run-book
    - `code/src/reports/generate_plots.py` — NOT invoked by the run-book
    - `code/src/reports/sensitivity.py` — NOT invoked by the run-book
    - `code/tests/unit/test_fit_t027.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/reports/sensitivity.py` — NOT invoked by the run-book
    - `code/tests/unit/test_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
