# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 9 declared deliverable(s) absent: data/interim/external_facts.json; data/interim/human_pilot_cleaned.csv; data/interim/labeled_responses.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/main.py", line 19, in <module>
    from validation import (
ImportError: cannot import name 'enforce_pipeline_limit' from 'validation' (/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/validation.py)


## Declared deliverables still missing

- data/interim/external_facts.json
- data/interim/human_pilot_cleaned.csv
- data/interim/labeled_responses.csv
- data/processed/features.csv
- data/raw/human_pilot_raw.csv
- data/raw/medmis_subset.csv
- data/raw/survey_payload.json
- data/results/feature_correlation_and_kappa.json
- data/results/pipeline_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/external_facts.json` is declared but was NOT written. Scripts referencing it:
    - `code/labeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/external_facts.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/human_pilot_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/annotation.py` — NOT invoked by the run-book
    - `code/validation_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/human_pilot_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/labeled_responses.csv` is declared but was NOT written. Scripts referencing it:
    - `code/labeling.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/labeled_responses.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/annotation.py` — NOT invoked by the run-book
    - `code/data_models.py` — NOT invoked by the run-book
    - `code/feature_save.py` — NOT invoked by the run-book
    - `code/features.py` — NOT invoked by the run-book
    - `code/labeling.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/merge_save.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/human_pilot_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/human_pilot_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/medmis_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/medmis_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/survey_payload.json` is declared but was NOT written. Scripts referencing it:
    - `code/annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/survey_payload.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/feature_correlation_and_kappa.json` is declared but was NOT written. Scripts referencing it:
    - `code/annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/feature_correlation_and_kappa.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pipeline_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/annotation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/pipeline_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
