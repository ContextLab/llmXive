# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/01_generate_networks.py --n 200 --types small_world,scale_free,random --seed 42; python code/02_compute_transport.py --input data/processed/graphs/ --mode cpu; python code/03_analyze_correlations.py --transport data/processed/transport/ --graphs data/processed/graphs/; 2 command(s) failed: python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/test_full_pipeline.py (rc=4); 3 declared deliverable(s) absent: data/analysis/sensitivity_results.csv; data/processed/pilot_data/pilot_metrics.csv; data/transport/transport_results.csv

## Failing / missing run-book commands

- python code/01_generate_networks.py --n 200 --types small_world,scale_free,random --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/01_generate_networks.py': [Errno 2] No such file or directory

- python code/02_compute_transport.py --input data/processed/graphs/ --mode cpu -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/02_compute_transport.py': [Errno 2] No such file or directory

- python code/03_analyze_correlations.py --transport data/processed/transport/ --graphs data/processed/graphs/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/03_analyze_correlations.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
r: No module named 'jsonschema'
=============================== warnings summary ===============================
code/utils/models.py:42
  /home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/utils/models.py:42: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    @validator("adjacency")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_check_connectivity_ci.py
ERROR tests/unit/test_generate_networks.py
ERROR tests/unit/test_power_analysis.py
ERROR tests/unit/test_power_analysis_verification.py
ERROR tests/unit/test_topological_metrics.py
ERROR tests/unit/test_transport_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 6 errors in 0.86s =========================


- python -m pytest tests/integration/test_full_pipeline.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.12.4, cov-7.1.0
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_full_pipeline.py



## Declared deliverables still missing

- data/analysis/sensitivity_results.csv
- data/processed/pilot_data/pilot_metrics.csv
- data/transport/transport_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/sensitivity_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_analysis_transport_loop.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pilot_data/pilot_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_pilot_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pilot_data/pilot_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/transport/transport_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_analysis_transport_loop.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/transport/transport_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
