# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data_ingestion.py (rc=1); python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/encoded_alloys.csv; data/processed/model_validation_report.json; data/processed/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/data_ingestion.py", line 6, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/main.py", line 8, in <module>
    from config import parse_cli_args, load_environment, get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/config.py", line 4, in <module>
    from dotenv import load_dotenv
ModuleNotFoundError: No module named 'dotenv'

## Declared deliverables still missing

- data/processed/encoded_alloys.csv
- data/processed/model_validation_report.json
- data/processed/sensitivity_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/encoded_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/pareto_optimization.py` — NOT invoked by the run-book
    - `code/cluster_analysis.py` — NOT invoked by the run-book
    - `code/model_training.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/encoded_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cluster_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
