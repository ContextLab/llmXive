# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/src/pipeline/run_analysis.py --step ingest (rc=1); python code/src/pipeline/run_analysis.py --full (rc=1); python -m pytest tests/contract/test_output_schema.py (rc=4); 1 declared deliverable(s) absent: data/processed/extreme_events.parquet

## Failing / missing run-book commands

- python code/src/pipeline/run_analysis.py --step ingest -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-303-statistical-analysis-of-publicly-availab/code/src/pipeline/run_analysis.py", line 10, in <module>
    from src.config import get_config
ModuleNotFoundError: No module named 'src.config'

- python code/src/pipeline/run_analysis.py --full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-303-statistical-analysis-of-publicly-availab/code/src/pipeline/run_analysis.py", line 10, in <module>
    from src.config import get_config
ModuleNotFoundError: No module named 'src.config'

- python -m pytest tests/contract/test_output_schema.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-303-statistical-analysis-of-publicly-availab/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-303-statistical-analysis-of-publicly-availab
configfile: pyproject.toml
plugins: platformdirs-4.13.0
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_output_schema.py



## Declared deliverables still missing

- data/processed/extreme_events.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/extreme_events.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/preprocessing.py` — NOT invoked by the run-book
    - `code/src/data/summary.py` — NOT invoked by the run-book
    - `code/src/models/gpd_baseline.py` — NOT invoked by the run-book
    - `code/src/scripts/generate_extreme_events_parquet.py` — NOT invoked by the run-book
    - `code/tests/unit/test_extreme_event_mapping.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_extreme_events_parquet.py` — NOT invoked by the run-book
    - `code/tests/unit/test_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extreme_events.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
