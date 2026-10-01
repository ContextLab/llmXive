# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/src/cli.py  --mode=secondary_analysis  --input=data/raw/public_dataset.csv  --output=data/processed/analysis_result.json (rc=1); python code/src/cli.py  --mode=synthetic  --n_participants=100  --effect_size=0.5  --output=data/synthetic/generated_dataset.csv (rc=1); python code/src/cli.py  --mode=secondary_analysis  --input=data/raw/public_dataset.csv  --sweep_thresholds=0.01,0.05,0.10  --output=data/processed/full_report.json (rc=1); 5 declared deliverable(s) absent: data/processed/perf_log.json; data/processed/results.json; data/processed/results_us2.json

## Failing / missing run-book commands

- python code/src/cli.py  --mode=secondary_analysis  --input=data/raw/public_dataset.csv  --output=data/processed/analysis_result.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-560-embodied-curriculum-learning-physical-si/code/src/cli.py", line 9, in <module>
    from .logging_config import setup_logging
ImportError: attempted relative import with no known parent package
- python code/src/cli.py  --mode=synthetic  --n_participants=100  --effect_size=0.5  --output=data/synthetic/generated_dataset.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-560-embodied-curriculum-learning-physical-si/code/src/cli.py", line 9, in <module>
    from .logging_config import setup_logging
ImportError: attempted relative import with no known parent package
- python code/src/cli.py  --mode=secondary_analysis  --input=data/raw/public_dataset.csv  --sweep_thresholds=0.01,0.05,0.10  --output=data/processed/full_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-560-embodied-curriculum-learning-physical-si/code/src/cli.py", line 9, in <module>
    from .logging_config import setup_logging
ImportError: attempted relative import with no known parent package

## Declared deliverables still missing

- data/processed/perf_log.json
- data/processed/results.json
- data/processed/results_us2.json
- data/processed/validated_fallback.csv
- data/synthetic/generated_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/perf_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_performance.py` — NOT invoked by the run-book
    - `code/src/cli.py` — IS a run-book command
    - `code/src/perf_monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perf_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/test_performance.py` — NOT invoked by the run-book
    - `code/tests/test_stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_results_aggregator.py` — NOT invoked by the run-book
    - `code/tests/test_quickstart_validation.py` — NOT invoked by the run-book
    - `code/src/cli.py` — IS a run-book command
    - `code/src/sensitivity.py` — NOT invoked by the run-book
    - `code/src/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results_us2.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/cli.py` — IS a run-book command
    - `code/src/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results_us2.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validated_fallback.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_performance.py` — NOT invoked by the run-book
    - `code/src/cli.py` — IS a run-book command
    - `code/src/data_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validated_fallback.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/synthetic/generated_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/cli.py` — IS a run-book command
  Make ONE of these WRITE `data/synthetic/generated_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
