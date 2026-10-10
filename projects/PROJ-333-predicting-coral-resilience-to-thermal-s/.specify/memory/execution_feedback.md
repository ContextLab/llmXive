# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/quantify.py --input data/raw --index data/reference_index --output data/processed; python code/enrichment.py; python code/viz.py; 2 command(s) failed: python code/ingest.py --project PRJNA321023 (rc=1); python -m pytest tests/ (rc=2); 2 declared deliverable(s) absent: data/raw/checksums.json; data/raw/download_log.json

## Failing / missing run-book commands

- python code/ingest.py --project PRJNA321023 -> rc=1
iled to load metadata: Phenotype metadata file not found: data/raw/phenotype_metadata.csv
2026-10-10 16:20:07,326 - ingest_t017 - ERROR - T017 Failed: Phenotype metadata file not found: data/raw/phenotype_metadata.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/ingest.py", line 266, in run_ingestion_phase_2
    valid_records, stats = parse_and_filter_phenotypes(
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/ingest.py", line 127, in parse_and_filter_phenotypes
    raw_metadata = load_phenotype_metadata()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/ingest.py", line 81, in load_phenotype_metadata
    raise IngestionError(f"Phenotype metadata file not found: {METADATA_FILE}")
IngestionError: Phenotype metadata file not found: data/raw/phenotype_metadata.csv
Error executing T017: Phenotype parsing failed: Phenotype metadata file not found: data/raw/phenotype_metadata.csv


- python code/quantify.py --input data/raw --index data/reference_index --output data/processed -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/quantify.py': [Errno 2] No such file or directory

- python code/enrichment.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/enrichment.py': [Errno 2] No such file or directory

- python code/viz.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/viz.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
to-thermal-s/code/utils/__init__.py)
__________________ ERROR collecting tests/unit/test_utils.py ___________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/tests/unit/test_utils.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_utils.py:11: in <module>
    from code.utils import (
E   ImportError: cannot import name 'setup_logger' from 'code.utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-333-predicting-coral-resilience-to-thermal-s/code/utils/__init__.py)
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline_flow.py
ERROR tests/unit/test_env_manager.py
ERROR tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 skipped, 3 errors in 0.70s =========================



## Declared deliverables still missing

- data/raw/checksums.json
- data/raw/download_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/download_reference.py` — NOT invoked by the run-book
    - `code/ingest.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/download_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/download_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
