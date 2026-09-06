# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json (rc=1); python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/ (rc=1); 5 declared deliverable(s) absent: data/processed/analysis_summary.json; data/processed/descriptors.csv; data/processed/feature_importance.csv

## Failing / missing run-book commands

- python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/model_training.py", line 138, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/model_training.py", line 33, in main
    parser = argparse.ArgumentParser(description="Train models on processed data.")
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/analysis.py", line 8, in <module>
    from statsmodels.stats.outlier_influence import variance_inflation_factor
ModuleNotFoundError: No module named 'statsmodels.stats.outlier_influence'

## Declared deliverables still missing

- data/processed/analysis_summary.json
- data/processed/descriptors.csv
- data/processed/feature_importance.csv
- data/processed/model_results.json
- data/processed/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/run_analysis_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_cross_validation.py` — NOT invoked by the run-book
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/descriptors.py` — IS a run-book command
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
