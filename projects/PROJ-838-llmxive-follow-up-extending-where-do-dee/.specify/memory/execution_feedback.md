# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/pipeline.py --config code/config.py; 13 declared deliverable(s) absent: data/processed/baseline_report.json; data/processed/comparative_report.json; data/processed/f1_max_threshold.json

## Failing / missing run-book commands

- python code/pipeline.py --config code/config.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/baseline_report.json
- data/processed/comparative_report.json
- data/processed/f1_max_threshold.json
- data/processed/linear_reasoning_report.json
- data/processed/metrics.csv
- data/processed/power_analysis.json
- data/processed/results_report.json
- data/processed/sc_002_result.json
- data/processed/sensitivity_percentile_matrix.json
- data/processed/sensitivity_threshold_matrix.json
- data/processed/test_metrics.csv
- data/processed/threshold_config.json
- data/processed/train_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/comparative_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/comparative_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/f1_max_threshold.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/f1_max_threshold.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/linear_reasoning_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/linear_reasoning_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
    - `code/run_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sc_002_result.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sc_002_result.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_percentile_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_percentile_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_threshold_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_threshold_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_evaluator.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
