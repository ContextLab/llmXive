# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --full (rc=1); python code/main.py --config "sample_size=50,distribution=normal,test=ttest,effect=0.0" (rc=1); 4 declared deliverable(s) absent: data/processed/error_rates.csv; data/processed/raw_pvalues.csv; data/processed/stability_trend.csv

## Failing / missing run-book commands

- python code/main.py --full -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/main.py", line 30, in <module>
    from run_data_gen import main as run_data_gen_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 3, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/main.py --config "sample_size=50,distribution=normal,test=ttest,effect=0.0" -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/main.py", line 30, in <module>
    from run_data_gen import main as run_data_gen_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 3, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/error_rates.csv
- data/processed/raw_pvalues.csv
- data/processed/stability_trend.csv
- data/raw/sample_validation.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/error_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_analyzer.py` — NOT invoked by the run-book
    - `code/export_results.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/simulation_engine.py` — NOT invoked by the run-book
    - `code/visualizer.py` — NOT invoked by the run-book
    - `code/run_simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/error_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_analyzer.py` — NOT invoked by the run-book
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/export_results.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/run_optimized_simulation.py` — NOT invoked by the run-book
    - `code/simulation_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stability_trend.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stability_trend.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sample_validation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_data_gen.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/sample_validation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
