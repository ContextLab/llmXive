# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/01_retrieve_data.py (rc=1); python code/02_preprocess.py (rc=1); python code/03_diversity.py (rc=1); 2 declared deliverable(s) absent: data/processed/power_analysis_report.json; data/processed/sample_size_validation.json

## Failing / missing run-book commands

- python code/01_retrieve_data.py -> rc=1
    2026-07-29 04:45:10,549 - INFO - Starting data retrieval process...
2026-07-29 04:45:10,549 - INFO - Validating configuration file: /home/runner/work/llmXive/llmXive/projects/PROJ-280-investigating-microbial-community-succes/data/config/dataset_ids.json
2026-07-29 04:45:10,549 - ERROR - CRITICAL DATA GAP: Error during validation: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-280-investigating-microbial-community-succes/data/contracts/dataset-config.schema.yaml
- python code/02_preprocess.py -> rc=1
    2026-07-29 04:45:11,322 - INFO - Starting Preprocessing Pipeline...
2026-07-29 04:45:11,322 - ERROR - CRITICAL DATA GAP: No feature table found in data/raw/
- python code/03_diversity.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-280-investigating-microbial-community-succes/code/03_diversity.py", line 11, in <module>
    from skbio.stats.distance import permanova, beta_diversity
ImportError: cannot import name 'beta_diversity' from 'skbio.stats.distance' (/home/runner/work/llmXive/llmXive/projects/PROJ-280-investigating-microbial-community-succes/code/.venv/lib/python3.11/site-packages/skbio/stats/distance/__init__.py)
- python code/04_network.py -> rc=1
    2026-07-29 04:45:13,388 - ERROR - Feature table not found. Ensure T012/T013 has run.
- python code/05_correlation.py -> rc=1
    2026-07-29 04:45:14,128 - ERROR - Required processed data files missing. Run T012/T013 first.

## Declared deliverables still missing

- data/processed/power_analysis_report.json
- data/processed/sample_size_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_diversity.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sample_size_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_diversity.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sample_size_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
