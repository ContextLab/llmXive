# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python -m code.ingest.download_nber (rc=1); python -m code.ingest.fetch_fred (rc=1); python -m code.ingest.fetch_sentiment   # only works if a verified sentiment URL has been added (rc=1); 3 declared deliverable(s) absent: data/metadata/recession_periods.json; data/processed/aligned_monthly.csv; data/processed/data_quality_log.json

## Failing / missing run-book commands

- python -m code.ingest.download_nber -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.download_nber' (ModuleNotFoundError: No module named 'code.ingest')

- python -m code.ingest.fetch_fred -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.fetch_fred' (ModuleNotFoundError: No module named 'code.ingest')

- python -m code.ingest.fetch_sentiment   # only works if a verified sentiment URL has been added -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.fetch_sentiment' (ModuleNotFoundError: No module named 'code.ingest')

- python -m code.ingest.sentiment_extraction -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.sentiment_extraction' (ModuleNotFoundError: No module named 'code.ingest')

- python -m code.ingest.merge_align -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.merge_align' (ModuleNotFoundError: No module named 'code.ingest')

- python -m code.ingest.validate_schema   # validates aligned_monthly.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.validate_schema' (ModuleNotFoundError: No module named 'code.ingest')

- python -m code.ingest.generate_merged    # creates and validates merged_timeseries.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-069-statistical-analysis-of-sentiment-drift-/bin/python: Error while finding module specification for 'code.ingest.generate_merged' (ModuleNotFoundError: No module named 'code.ingest')


## Declared deliverables still missing

- data/metadata/recession_periods.json
- data/processed/aligned_monthly.csv
- data/processed/data_quality_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/recession_periods.json` is declared but was NOT written. Scripts referencing it:
    - `code/contracts/__init__.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/recession_periods.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_monthly.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_quality_report.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_monthly.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/data_quality_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_quality_report.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/data_quality_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
