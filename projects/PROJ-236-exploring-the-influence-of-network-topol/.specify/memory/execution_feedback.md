# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/01_generate_networks.py --n 200 --types small_world,scale_free,random --seed 42; python code/02_compute_transport.py --input data/processed/graphs/ --mode cpu; python code/03_analyze_correlations.py --transport data/processed/transport/ --graphs data/processed/graphs/; 3 declared deliverable(s) absent: data/analysis/sensitivity_results.csv; data/processed/pilot_data/pilot_metrics.csv; data/transport/transport_results.csv

## Failing / missing run-book commands

- python code/01_generate_networks.py --n 200 --types small_world,scale_free,random --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/01_generate_networks.py': [Errno 2] No such file or directory
- python code/02_compute_transport.py --input data/processed/graphs/ --mode cpu -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/02_compute_transport.py': [Errno 2] No such file or directory
- python code/03_analyze_correlations.py --transport data/processed/transport/ --graphs data/processed/graphs/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-236-exploring-the-influence-of-network-topol/code/03_analyze_correlations.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/analysis/sensitivity_results.csv
- data/processed/pilot_data/pilot_metrics.csv
- data/transport/transport_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/sensitivity_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_analysis_transport_loop.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/sensitivity_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pilot_data/pilot_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_pilot_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pilot_data/pilot_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/transport/transport_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity_analysis_transport_loop.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/transport/transport_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
