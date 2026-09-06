# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python analysis/clustering.py`
- `python analysis/feasibility_check.py`
- `python analysis/sensitivity.py`
- `python ingestion/encode_composition.py`
- `python ingestion/load_oqmd.py`
- `python modeling/pareto_optimize.py`
- `python modeling/train_surrogates.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python ingestion/load_oqmd.py; python ingestion/encode_composition.py; python modeling/train_surrogates.py; 1 command(s) failed: python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/encoded_alloys.csv; data/processed/model_validation_report.json; data/processed/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/main.py", line 15, in <module>
    from model_validation import generate_validation_report, save_validation_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/model_validation.py", line 12, in <module>
    from models.alloy_entry import AlloyEntry
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/models/__init__.py", line 4, in <module>
    from .alloy_entry import AlloyEntry, ElementDescriptor
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/models/alloy_entry.py", line 2, in <module>
    from pydantic import BaseModel, Field, field_validator, model_validator
ImportError: cannot import name 'field_validator' from 'pydantic' (/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/lib/python3.11/site-packages/pydantic/__init__.cpython-311-x86_64-linux-gnu.so)
- python ingestion/load_oqmd.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/ingestion/load_oqmd.py': [Errno 2] No such file or directory
- python ingestion/encode_composition.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/ingestion/encode_composition.py': [Errno 2] No such file or directory
- python modeling/train_surrogates.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/modeling/train_surrogates.py': [Errno 2] No such file or directory
- python analysis/feasibility_check.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/analysis/feasibility_check.py': [Errno 2] No such file or directory
- python analysis/clustering.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/analysis/clustering.py': [Errno 2] No such file or directory
- python analysis/sensitivity.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/analysis/sensitivity.py': [Errno 2] No such file or directory
- python modeling/pareto_optimize.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/modeling/pareto_optimize.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/encoded_alloys.csv
- data/processed/model_validation_report.json
- data/processed/sensitivity_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/encoded_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/feature_encoder.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/metrics_calculation.py` — NOT invoked by the run-book
    - `code/cluster_analysis.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/pareto_optimization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/encoded_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/model_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cluster_analysis.py` — NOT invoked by the run-book
    - `code/robustness_validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
