# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/main.py --seed 42; 6 declared deliverable(s) absent: data/cleaned/merged_perovskite.csv; data/cleaned/provenance_report.json; data/descriptors.csv

## Failing / missing run-book commands

- python src/main.py --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-035-exploring-the-correlation-between-crysta/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-035-exploring-the-correlation-between-crysta/src/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/cleaned/merged_perovskite.csv
- data/cleaned/provenance_report.json
- data/descriptors.csv
- data/raw/thermal_raw.csv
- data/results/correlation_matrix.json
- data/results/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/cleaned/merged_perovskite.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/cleaning/provenance_validator.py` — NOT invoked by the run-book
    - `code/tests/contract/test_schema.py` — NOT invoked by the run-book
    - `code/tests/integration/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/src/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/src/descriptors/compute_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/cleaned/merged_perovskite.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/cleaned/provenance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/cleaning/provenance_validator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_provenance_validator.py` — NOT invoked by the run-book
    - `code/src/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/src/cleaning/provenance_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/cleaned/provenance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_descriptors.py` — NOT invoked by the run-book
    - `code/src/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/src/analysis/stratify.py` — NOT invoked by the run-book
    - `code/src/analysis/run_vif_check.py` — NOT invoked by the run-book
    - `code/src/descriptors/compute_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/thermal_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_provenance_validator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_temperature_normalize.py` — NOT invoked by the run-book
    - `code/src/cleaning/provenance_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/thermal_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_correlation.py` — NOT invoked by the run-book
    - `code/src/utils/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_sensitivity.py` — NOT invoked by the run-book
    - `code/src/utils/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/run_sensitivity_exec.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
