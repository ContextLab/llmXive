# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/verify_hf_dataset.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/verify_hf_dataset.py; 1 command(s) failed: python code/run_pipeline_timing.py (rc=1); 7 declared deliverable(s) absent: data/artifacts/shap_summary.png; data/processed/step_final_cleaned.csv; data/raw/test_n.csv

## Failing / missing run-book commands

- python code/verify_hf_dataset.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/verify_hf_dataset.py': [Errno 2] No such file or directory
- python code/run_pipeline_timing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/run_pipeline_timing.py", line 18, in <module>
    from ingestion import main as run_ingestion
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/ingestion.py", line 13, in <module>
    from periodictable import elements
ModuleNotFoundError: No module named 'periodictable'

## Declared deliverables still missing

- data/artifacts/shap_summary.png
- data/processed/step_final_cleaned.csv
- data/raw/test_n.csv
- data/reports/data_availability_report.json
- data/results/descriptor_sufficiency.json
- data/results/fold_importances.json
- data/results/stability_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/shap_summary.png` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/shap_summary.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/step_final_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/scripts/run_gap_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/step_final_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/test_n.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/scripts/create_test_n_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/test_n.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/reports/data_availability_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/data_availability_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/descriptor_sufficiency.json` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/descriptor_sufficiency.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/fold_importances.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fold_importances.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — NOT invoked by the run-book
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
