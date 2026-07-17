# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py --config code/config.yaml --output data/; 6 declared deliverable(s) absent: data/analysis/final_results.json; data/analysis/power_analysis_report.json; data/analysis/sensitivity_sweep.json

## Failing / missing run-book commands

- python code/main.py --config code/config.yaml --output data/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-326-investigating-the-impact-of-network-stru/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/analysis/final_results.json
- data/analysis/power_analysis_report.json
- data/analysis/sensitivity_sweep.json
- data/analysis/simulation_results.json
- data/raw/global_batch_manifest.json
- data/run_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/final_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_run_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/final_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/plotting.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/report.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/src/analysis/__init__.py` — NOT invoked by the run-book
    - `code/scripts/validate_batch.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/simulation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/simulation/serialization.py` — NOT invoked by the run-book
    - `code/src/simulation/schema.py` — NOT invoked by the run-book
    - `code/src/simulation/run_simulation.py` — NOT invoked by the run-book
    - `code/src/analysis/plotting.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/anova.py` — NOT invoked by the run-book
    - `code/src/analysis/run_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_serialization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/simulation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/global_batch_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/generators/aggregate_batch.py` — NOT invoked by the run-book
    - `code/scripts/validate_batch.py` — NOT invoked by the run-book
    - `code/tests/test_aggregate_batch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/global_batch_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/run_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/logging.py` — NOT invoked by the run-book
    - `code/src/utils/reproducibility.py` — NOT invoked by the run-book
    - `code/src/generators/aggregate_batch.py` — NOT invoked by the run-book
    - `code/scripts/test_logging_demo.py` — NOT invoked by the run-book
    - `code/scripts/verify_config_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_logging.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_generators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/run_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
