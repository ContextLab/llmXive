# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/results/pipeline_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/results/pipeline_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 command(s) failed: python code/main.py (rc=1); 8 declared deliverable(s) absent: data/interim/external_facts.json; data/interim/human_pilot_cleaned.csv; data/interim/labeled_responses.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/main.py", line 185, in main
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/main.py", line 90, in run_ingestion
    from ingestion import main as ingestion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/ingestion.py", line 21, in <module>
    raise ImportError("The 'datasets' package is required. Install with: pip install datasets")
ImportError: The 'datasets' package is required. Install with: pip install datasets


## Declared deliverables still missing

- data/interim/external_facts.json
- data/interim/human_pilot_cleaned.csv
- data/interim/labeled_responses.csv
- data/processed/features.csv
- data/raw/human_pilot_raw.csv
- data/raw/medmis_subset.csv
- data/raw/survey_payload.json
- data/results/feature_correlation_and_kappa.json

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
