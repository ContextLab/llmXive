# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest tests/ -v --cov=src (rc=2); 3 declared deliverable(s) absent: data/derived/reference/kappa_values.csv; data/metadata/manual_reference.json; data/metadata/valid_sources.json

## Failing / missing run-book commands

- python -m pytest tests/ -v --cov=src -> rc=2
ator.py         144    144     0%   1-246
src/services/run_registry_validator.py       8      8     0%   7-18
src/services/topology_extractor.py         201    201     0%   1-408
----------------------------------------------------------------------
TOTAL                                      696    696     0%

FAIL Required test coverage of 70% not reached. Total coverage: 0.00%
=========================== short test summary info ============================
ERROR tests/contract/test_topology_schema.py
ERROR tests/unit/test_registry_generator.py
ERROR tests/unit/test_registry_validator.py
ERROR tests/unit/test_simulation_box.py
ERROR tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 5 errors in 0.72s =========================

/home/runner/work/llmXive/llmXive/projects/PROJ-260-investigating-the-influence-of-network-s/code/.venv/lib/python3.11/site-packages/coverage/control.py:967: CoverageWarning: No data was collected. (no-data-collected); see https://coverage.readthedocs.io/en/7.16.2/messages.html#warning-no-data-collected
  self._warn("No data was collected.", slug="no-data-collected")


## Declared deliverables still missing

- data/derived/reference/kappa_values.csv
- data/metadata/manual_reference.json
- data/metadata/valid_sources.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/reference/kappa_values.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/services/data_aggregator.py` — NOT invoked by the run-book
    - `code/src/services/independence_validator.py` — NOT invoked by the run-book
    - `code/src/services/kappa_ingester.py` — NOT invoked by the run-book
    - `code/src/services/reference_generator.py` — NOT invoked by the run-book
    - `code/tests/integration/test_data_aggregator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_kappa_ingester.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/reference/kappa_values.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metadata/manual_reference.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_manual_reference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/manual_reference.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metadata/valid_sources.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/services/kappa_ingester.py` — NOT invoked by the run-book
    - `code/tests/unit/test_kappa_ingester.py` — NOT invoked by the run-book
    - `src/services/registry_validator.py` — NOT invoked by the run-book
    - `src/services/run_registry_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/valid_sources.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
