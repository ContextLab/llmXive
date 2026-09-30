# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 6 declared deliverable(s) absent: data/artifacts/baseline_comparison.json; data/artifacts/fidelity_report.json; data/artifacts/resource_log.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-485-predicting-alloy-phase-diagrams-from-com/code/main.py", line 10, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/artifacts/baseline_comparison.json
- data/artifacts/fidelity_report.json
- data/artifacts/resource_log.json
- data/artifacts/tcs_report.json
- data/processed/descriptors.csv
- data/raw/elemental_properties.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/baseline_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/permutation_test.py` — NOT invoked by the run-book
    - `code/models/null_baseline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/baseline_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/fidelity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/viz/plot_phase_diagrams.py` — NOT invoked by the run-book
    - `code/viz/fidelity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/fidelity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/resource_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/resource_monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/resource_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/tcs_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/viz/topological_consistency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/tcs_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/features/export_descriptors.py` — NOT invoked by the run-book
    - `code/features/generate_descriptors.py` — NOT invoked by the run-book
    - `code/models/null_baseline.py` — NOT invoked by the run-book
    - `code/models/train.py` — NOT invoked by the run-book
    - `code/viz/topological_consistency.py` — NOT invoked by the run-book
    - `code/viz/plot_phase_diagrams.py` — NOT invoked by the run-book
    - `code/ingest/load_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/elemental_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features/verify_elements.py` — NOT invoked by the run-book
    - `code/features/generate_descriptors.py` — NOT invoked by the run-book
    - `code/models/loso_checks.py` — NOT invoked by the run-book
    - `code/viz/topological_consistency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/elemental_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
