# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python main.py; 2 command(s) failed: python -m src.ingestion.fetch_nist   # pulls NIST CSV from the verified HuggingFace URL (rc=1); python -m src.ingestion.fetch_journal   # pulls the journal supplement CSV (you must provide the DOI in `config.yaml`) (rc=1); 2 declared deliverable(s) absent: data/raw/manual_curated.csv; data/results/demo_metrics.json

## Failing / missing run-book commands

- python -m src.ingestion.fetch_nist   # pulls NIST CSV from the verified HuggingFace URL -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-393-predicting-the-influence-of-composition-/bin/python: No module named src.ingestion.fetch_nist

- python -m src.ingestion.fetch_journal   # pulls the journal supplement CSV (you must provide the DOI in `config.yaml`) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-393-predicting-the-influence-of-composition-/bin/python: No module named src.ingestion.fetch_journal

- python main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-393-predicting-the-influence-of-composition-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-393-predicting-the-influence-of-composition-/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/manual_curated.csv
- data/results/demo_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/manual_curated.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_manual_curator.py` — NOT invoked by the run-book
    - `code/scripts/verify_artifacts.py` — NOT invoked by the run-book
    - `code/src/ingestion/ingest_pipeline.py` — NOT invoked by the run-book
    - `code/src/ingestion/manual_curator.py` — NOT invoked by the run-book
    - `code/src/preprocessing/preprocess_pipeline.py` — NOT invoked by the run-book
    - `code/src/validation/imputation_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/integration/test_manual_curator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_manual_curation_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/manual_curated.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/demo_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/demo_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
