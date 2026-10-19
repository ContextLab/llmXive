# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/data/validate_metadata.py (rc=1); 15 declared deliverable(s) absent: data/processed/behavioral/fd_mean.csv; data/processed/behavioral/power_metrics.json; data/processed/behavioral/retention_metrics.json

## Failing / missing run-book commands

- python code/data/validate_metadata.py -> rc=1
Download module loaded.

2026-10-19 00:46:08,832 INFO __main__: Metadata missing; re-running T001 downloader /home/runner/work/llmXive/llmXive/projects/PROJ-377-investigating-the-impact-of-network-cent/code/data/download.py
2026-10-19 00:46:08,946 ERROR __main__: Fatal: Metadata file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-377-investigating-the-impact-of-network-cent/data/raw/metadata.csv


## Declared deliverables still missing

- data/processed/behavioral/fd_mean.csv
- data/processed/behavioral/power_metrics.json
- data/processed/behavioral/retention_metrics.json
- data/processed/behavioral/subject_scores.csv
- data/processed/centrality/global_scores.csv
- data/processed/centrality/model_predictors.csv
- data/processed/centrality/subject_id_metrics.csv
- data/processed/centrality/vif_values.csv
- data/processed/logs/exclusion_log.csv
- data/processed/regression/linear_model_summary.csv
- data/processed/validation/cv_results.json
- data/processed/validation/null_distribution.csv
- data/processed/validation/null_residuals.csv
- data/processed/validation/permutation_results.json
- data/raw/metadata.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/behavioral/fd_mean.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/behavioral/fd_mean.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/behavioral/power_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/power_check.py` — NOT invoked by the run-book
    - `code/data/power_logging.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/behavioral/power_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/behavioral/retention_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/exclusion_logging.py` — NOT invoked by the run-book
    - `code/data/power_check.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/retention_validation.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/behavioral/retention_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/behavioral/subject_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/optimization_pipeline.py` — NOT invoked by the run-book
    - `code/data/behavioral_extraction.py` — NOT invoked by the run-book
    - `code/data/exclusion_logging.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/behavioral/subject_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/centrality/global_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/centrality/global_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/centrality/model_predictors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/optimization_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/centrality/model_predictors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/centrality/subject_id_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/optimization_pipeline.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/centrality/subject_id_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/centrality/vif_values.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/centrality/vif_values.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/logs/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/exclusion.py` — NOT invoked by the run-book
    - `code/data/behavioral_extraction.py` — NOT invoked by the run-book
    - `code/data/exclusion_logging.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/logs/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression/linear_model_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/optimization_pipeline.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/utils/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression/linear_model_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation/cv_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/utils/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation/cv_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation/null_distribution.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/optimization_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation/null_distribution.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation/null_residuals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation/null_residuals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/utils/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/behavioral_extraction.py` — NOT invoked by the run-book
    - `code/data/exclusion_logging.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/retention_validation.py` — NOT invoked by the run-book
    - `code/data/validate_metadata.py` — IS a run-book command
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/validation_gate.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
