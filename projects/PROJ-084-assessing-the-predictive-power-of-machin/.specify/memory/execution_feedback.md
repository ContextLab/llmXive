# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 2 command(s) failed: python -m pytest tests/ (rc=2); python -m pytest tests/contract/ (rc=2); 5 declared deliverable(s) absent: data/processed/cleaned_reactions.parquet; data/processed/sanitized_reactions.parquet; data/processed/scaffold_groups.parquet

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-084-assessing-the-predictive-power-of-machin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-084-assessing-the-predictive-power-of-machin/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
oduleNotFoundError: No module named 'rdkit'
=========================== short test summary info ============================
ERROR tests/contract/test_dataset_schema.py
ERROR tests/integration/test_batch_processing.py
ERROR tests/integration/test_evaluation.py
ERROR tests/integration/test_generalization.py
ERROR tests/integration/test_ingest_pipeline.py
ERROR tests/integration/test_orchestration.py
ERROR tests/integration/test_permutation_importance.py
ERROR tests/integration/test_save_models.py
ERROR tests/integration/test_split_logging.py
ERROR tests/integration/test_split_pipeline.py
ERROR tests/integration/test_training_pipeline.py
ERROR tests/unit/test_fingerprints.py
ERROR tests/unit/test_fingerprints_chunked.py
ERROR tests/unit/test_ingest_logging.py
ERROR tests/unit/test_memory_profiler.py
ERROR tests/unit/test_permutation_importance.py
ERROR tests/unit/test_sanitize.py
ERROR tests/unit/test_save_models.py
ERROR tests/unit/test_scaffold.py
ERROR tests/unit/test_validators.py
ERROR tests/unit/test_yield_parsing.py
!!!!!!!!!!!!!!!!!!! Interrupted: 21 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 21 errors in 1.16s ==============================


- python -m pytest tests/contract/ -> rc=2
==================== ERRORS ====================================
____________ ERROR collecting tests/contract/test_dataset_schema.py ____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-084-assessing-the-predictive-power-of-machin/tests/contract/test_dataset_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_dataset_schema.py:13: in <module>
    from utils.schema_validator import (
code/utils/__init__.py:2: in <module>
    from .io import (
E   ImportError: cannot import name 'validate_memory_requirements' from 'utils.io' (/home/runner/work/llmXive/llmXive/projects/PROJ-084-assessing-the-predictive-power-of-machin/code/utils/io.py)
=========================== short test summary info ============================
ERROR tests/contract/test_dataset_schema.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.29s ===============================



## Declared deliverables still missing

- data/processed/cleaned_reactions.parquet
- data/processed/sanitized_reactions.parquet
- data/processed/scaffold_groups.parquet
- data/raw/uspto_raw.parquet
- data/results/runtime_profile.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_reactions.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/split.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
    - `code/modeling/train_bounded.py` — NOT invoked by the run-book
    - `code/preprocessing/batch_processor.py` — NOT invoked by the run-book
    - `code/preprocessing/fingerprints.py` — NOT invoked by the run-book
    - `code/preprocessing/ingest.py` — NOT invoked by the run-book
    - `code/preprocessing/scaffold.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_reactions.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sanitized_reactions.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing/fingerprints.py` — NOT invoked by the run-book
    - `code/preprocessing/sanitize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sanitized_reactions.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaffold_groups.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/split.py` — NOT invoked by the run-book
    - `code/preprocessing/analyze_scaffolds.py` — NOT invoked by the run-book
    - `code/preprocessing/scaffold.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scaffold_groups.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/uspto_raw.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing/download.py` — NOT invoked by the run-book
    - `code/preprocessing/ingest.py` — NOT invoked by the run-book
    - `code/preprocessing/sanitize.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/uspto_raw.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_profile.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/aggregate_profiles.py` — NOT invoked by the run-book
    - `code/modeling/generate_final_report.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
    - `code/utils/memory_profiler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/runtime_profile.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
