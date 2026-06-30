# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py --num-tasks 100 --output-dir data/processed (rc=1); 4 declared deliverable(s) absent: data/benchmarks/processed/catalog.json; data/processed/corrected_pvalues.csv; data/processed/sensitivity_report.csv

## Failing / missing run-book commands

- python code/main.py --num-tasks 100 --output-dir data/processed -> rc=1
    /work/llmXive/llmXive/projects/PROJ-306-evaluating-the-impact-of-llm-generated-c/code/main.py", line 10, in <module>
    from config import resolve_model, get_fallback_models, get_primary_model
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-306-evaluating-the-impact-of-llm-generated-c/code/config.py", line 11, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/benchmarks/processed/catalog.json
- data/processed/corrected_pvalues.csv
- data/processed/sensitivity_report.csv
- data/processed/stats_summary.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/benchmarks/processed/catalog.json` is declared but was NOT written. Scripts referencing it:
    - `code/dataset_loader.py` — NOT invoked by the run-book
    - `code/test_transformer.py` — NOT invoked by the run-book
    - `code/task_t050_validate_quickstart.py` — NOT invoked by the run-book
    - `code/stratifier.py` — NOT invoked by the run-book
    - `code/coverage_runner.py` — NOT invoked by the run-book
    - `code/visualizer.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/benchmarks/processed/catalog.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/corrected_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corrected_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stats_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stats_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
