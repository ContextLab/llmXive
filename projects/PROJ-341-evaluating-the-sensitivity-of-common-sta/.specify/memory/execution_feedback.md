# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py (rc=1); python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 (rc=1); python code/main.py --mode validation (rc=1); 7 declared deliverable(s) absent: data/simulation/error_rates_summary.csv; data/simulation/p_values_raw.csv; data/simulation/real_data_power.json

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 23, in <module>
    from code.analysis.aggregator import main as aggregator_main, load_p_values_raw_safe, save_aggregated_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/aggregator.py", line 17, in <module>
    from code.simulation.output_writer import load_p_values_raw, load_p_values_raw_safe
ImportError: cannot import name 'load_p_values_raw_safe' from 'code.simulation.output_writer' (/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/simulation/output_writer.py)

- python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 23, in <module>
    from code.analysis.aggregator import main as aggregator_main, load_p_values_raw_safe, save_aggregated_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/aggregator.py", line 17, in <module>
    from code.simulation.output_writer import load_p_values_raw, load_p_values_raw_safe
ImportError: cannot import name 'load_p_values_raw_safe' from 'code.simulation.output_writer' (/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/simulation/output_writer.py)

- python code/main.py --mode validation -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 23, in <module>
    from code.analysis.aggregator import main as aggregator_main, load_p_values_raw_safe, save_aggregated_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/aggregator.py", line 17, in <module>
    from code.simulation.output_writer import load_p_values_raw, load_p_values_raw_safe
ImportError: cannot import name 'load_p_values_raw_safe' from 'code.simulation.output_writer' (/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/simulation/output_writer.py)


## Declared deliverables still missing

- data/simulation/error_rates_summary.csv
- data/simulation/p_values_raw.csv
- data/simulation/real_data_power.json
- data/simulation/real_data_pvalues.csv
- data/simulation/thresholds.json
- data/simulation/validation_metrics.json
- data/simulation_metadata.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/simulation/error_rates_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/visualization/comparative_plots.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/error_rates_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/p_values_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/simulation/output_writer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/p_values_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_power.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_power.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/analysis/real_data_runner.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/validator.py` — NOT invoked by the run-book
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/thresholds.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/thresholds.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_pipeline_steps.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/utils/checksum_utils.py` — NOT invoked by the run-book
    - `code/utils/metadata_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
