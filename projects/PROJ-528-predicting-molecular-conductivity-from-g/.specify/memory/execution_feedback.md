# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 7 declared deliverable(s) absent: data/processed/analysis_summary.json; data/processed/corr_plot_top5.png; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/analysis_summary.json
- data/processed/corr_plot_top5.png
- data/processed/descriptors.csv
- data/processed/feature_importance.csv
- data/processed/model_results.json
- data/processed/sensitivity_analysis.json
- data/raw/smiles.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/run_analysis_summary.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/validators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/corr_plot_top5.png` is declared but was NOT written. Scripts referencing it:
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corr_plot_top5.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_cross_validation.py` — NOT invoked by the run-book
    - `code/run_descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/run_analysis.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/validators.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_huckel_vif_loop.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/smiles.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/vif_iterative_retrain.py` — NOT invoked by the run-book
    - `code/outlier_sensitivity.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/validators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/smiles.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
