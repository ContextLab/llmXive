# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/`
  - script usage: `analysis.py [-h] [--data DATA] [--output OUTPUT]`
  - argparse error: `analysis.py: error: unrecognized arguments: --results data/processed/model_results.json --plots data/processed/correlation_plots/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json (rc=1); python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/ (rc=2); 6 declared deliverable(s) absent: data/processed/analysis_summary.json; data/processed/corr_plot_top5.png; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/model_training.py --data data/processed/descriptors.csv --output data/processed/model_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/model_training.py", line 221, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/model_training.py", line 199, in main
    logger.info(f"Loading data from {args.data}")
    ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'info'
- python code/analysis.py --results data/processed/model_results.json --plots data/processed/correlation_plots/ -> rc=2
    usage: analysis.py [-h] [--data DATA] [--output OUTPUT]
                   [--thresholds THRESHOLDS [THRESHOLDS ...]]
analysis.py: error: unrecognized arguments: --results data/processed/model_results.json --plots data/processed/correlation_plots/

## Declared deliverables still missing

- data/processed/analysis_summary.json
- data/processed/corr_plot_top5.png
- data/processed/descriptors.csv
- data/processed/feature_importance.csv
- data/processed/model_results.json
- data/processed/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/run_analysis_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/corr_plot_top5.png` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corr_plot_top5.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models.py` — NOT invoked by the run-book
    - `code/model_training.py` — IS a run-book command
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_cross_validation.py` — NOT invoked by the run-book
    - `code/descriptors.py` — IS a run-book command
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
    - `code/run_analysis_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
