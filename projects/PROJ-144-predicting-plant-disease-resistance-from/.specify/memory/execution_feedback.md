# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/preprocess.py --input data/raw --output data/processed (rc=1); python code/modeling/interpret.py --input results/shap_analysis.json --output results/pathway_analysis.json (rc=1); 3 declared deliverable(s) absent: data/processed/heterogeneity_report.json; data/processed/temporal_validation_log.json; data/raw/study_manifest.json

## Failing / missing run-book commands

- python code/data/preprocess.py --input data/raw --output data/processed -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-144-predicting-plant-disease-resistance-from/code/data/preprocess.py", line 13, in <module>
    from utils.exceptions import DataUnavailableError
ImportError: cannot import name 'DataUnavailableError' from 'utils.exceptions' (/home/runner/work/llmXive/llmXive/projects/PROJ-144-predicting-plant-disease-resistance-from/code/utils/exceptions.py)
- python code/modeling/interpret.py --input results/shap_analysis.json --output results/pathway_analysis.json -> rc=1
    2026-09-03 12:59:23,372 - __main__ - INFO - Starting T026c: Generating pathway interpretation report.
2026-09-03 12:59:23,372 - __main__ - INFO - Loading top metabolites from /home/runner/work/llmXive/llmXive/projects/PROJ-144-predicting-plant-disease-resistance-from/results/top_metabolites.json
2026-09-03 12:59:23,372 - __main__ - ERROR - Required input file missing: /home/runner/work/llmXive/llmXive/projects/PROJ-144-predicting-plant-disease-resistance-from/results/top_metabolites.json
2026-09-03 12:59:23,372 - __main__ - ERROR - Ensure T026a has completed successfully.

## Declared deliverables still missing

- data/processed/heterogeneity_report.json
- data/processed/temporal_validation_log.json
- data/raw/study_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/heterogeneity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/detect_label_heterogeneity.py` — NOT invoked by the run-book
    - `code/data/harmonize_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/heterogeneity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/temporal_validation_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_temporal.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/temporal_validation_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/study_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/match_and_download.py` — NOT invoked by the run-book
    - `code/data/validate_temporal.py` — NOT invoked by the run-book
    - `code/data/discover_studies.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/research/verify_studies.py` — NOT invoked by the run-book
    - `code/research/verify_artifact_tracking.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/study_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
