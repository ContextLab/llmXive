# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0; python code/analysis.py --validate-schema --input data/results/simulation_summary.csv; python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png; 2 declared deliverable(s) absent: data/results/simulation_summary.csv; data/results/us1_verification.json

## Failing / missing run-book commands

- python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/run_simulation.py': [Errno 2] No such file or directory
- python code/analysis.py --validate-schema --input data/results/simulation_summary.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis.py': [Errno 2] No such file or directory
- python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/visualization.py': [Errno 2] No such file or directory
- python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/visualization.py': [Errno 2] No such file or directory
- python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/visualization.py': [Errno 2] No such file or directory
- python code/analysis.py --verify-sensitivity --input data/results/sensitivity_analysis.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/simulation_summary.csv
- data/results/us1_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/simulation_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/schema_validator.py` — NOT invoked by the run-book
    - `code/analysis/aggregation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/simulation_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us1_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/simulation/verify_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us1_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
