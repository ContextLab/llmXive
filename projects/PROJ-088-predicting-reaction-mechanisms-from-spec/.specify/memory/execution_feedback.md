# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python -m src.cli.main run --seed 42 --max-rows 5000 (rc=1); python -m src.cli.main ingest (rc=1); python -m src.cli.modeling train (rc=1); 4 declared deliverable(s) absent: data/checksums.json; data/processed/fingerprints.parquet; data/reference/bin_mapping.json

## Failing / missing run-book commands

- python -m src.cli.main run --seed 42 --max-rows 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-088-predicting-reaction-mechanisms-from-spec/bin/python: No module named src.cli.main

- python -m src.cli.main ingest -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-088-predicting-reaction-mechanisms-from-spec/bin/python: No module named src.cli.main

- python -m src.cli.modeling train -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-088-predicting-reaction-mechanisms-from-spec/bin/python: No module named src.cli.modeling

- python -m src.cli.analysis run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-088-predicting-reaction-mechanisms-from-spec/bin/python: No module named src.cli.analysis

- python -m src.utils.io check_balance data/processed/fingerprints.parquet -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-088-predicting-reaction-mechanisms-from-spec/bin/python: No module named src.utils.io

- python -m src.utils.io check_significance data/processed/model_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-088-predicting-reaction-mechanisms-from-spec/bin/python: No module named src.utils.io

- python -m pytest tests/ -> rc=2


==================================== ERRORS ====================================
__________ ERROR collecting tests/integration/test_ingestion_flow.py ___________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-088-predicting-reaction-mechanisms-from-spec/tests/integration/test_ingestion_flow.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_ingestion_flow.py:24: in <module>
    from src.ingestion.preprocess import preprocess_dataset, bin_spectrum, normalize_spectrum
src/ingestion/__init__.py:11: in <module>
    from .load_nist import load_nist_data, main as load_nist_main
E   ModuleNotFoundError: No module named 'src.ingestion.load_nist'
=========================== short test summary info ============================
ERROR tests/integration/test_ingestion_flow.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.76s ===============================



## Declared deliverables still missing

- data/checksums.json
- data/processed/fingerprints.parquet
- data/reference/bin_mapping.json
- data/reference/literature_vibrational_modes.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/calculate_dataset_checksums.py` — NOT invoked by the run-book
    - `code/src/utils/checksum_manager.py` — NOT invoked by the run-book
    - `code/src/utils/io.py` — NOT invoked by the run-book
    - `code/tests/unit/test_checksum_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/fingerprints.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/calculate_dataset_checksums.py` — NOT invoked by the run-book
    - `code/src/ingestion/merge_spectra.py` — NOT invoked by the run-book
    - `code/tests/integration/test_merge_spectra.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fingerprints.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/reference/bin_mapping.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/bin_mapping.py` — NOT invoked by the run-book
    - `code/src/ingestion/merge_spectra.py` — NOT invoked by the run-book
    - `code/tests/integration/test_merge_spectra.py` — NOT invoked by the run-book
    - `code/tests/unit/test_bin_mapping.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reference/bin_mapping.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/reference/literature_vibrational_modes.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/research/fetch_literature_modes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reference/literature_vibrational_modes.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
