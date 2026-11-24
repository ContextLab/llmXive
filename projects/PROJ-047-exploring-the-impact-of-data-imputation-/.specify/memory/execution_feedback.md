# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png`
  - script usage: `visualization.py [-h]`
  - argparse error: `visualization.py: error: unrecognized arguments: --plot`
- run-book command: `python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png`
  - script usage: `visualization.py [-h]`
  - argparse error: `visualization.py: error: unrecognized arguments: --plot`
- run-book command: `python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png`
  - script usage: `visualization.py [-h]`
  - argparse error: `visualization.py: error: unrecognized arguments: --plot`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python -m pytest tests/unit/ -v (rc=4); python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0 (rc=1); python code/analysis.py --validate-schema --input data/results/simulation_summary.csv (rc=1); 6 declared deliverable(s) absent: data/results/power_analysis.json; data/results/sensitivity_analysis.json; data/results/sensitivity_analysis_dataset.csv

## Failing / missing run-book commands

- python -m pytest tests/unit/ -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-047-exploring-the-impact-of-data-imputation-/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/


- python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/run_simulation.py", line 11, in <module>
    from analysis.pipeline import run_imputation_and_estimation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/pipeline.py", line 16, in <module>
    from .causal_estimation import estimate_ate_ipw, estimate_ate_psm
ImportError: cannot import name 'estimate_ate_ipw' from 'analysis.causal_estimation' (/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/causal_estimation.py)

- python code/analysis.py --validate-schema --input data/results/simulation_summary.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis.py", line 12, in <module>
    from analysis.pipeline import run_imputation_and_estimation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/pipeline.py", line 16, in <module>
    from .causal_estimation import estimate_ate_ipw, estimate_ate_psm
ImportError: cannot import name 'estimate_ate_ipw' from 'analysis.causal_estimation' (/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/causal_estimation.py)

- python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png -> rc=2

usage: visualization.py [-h]
                        {bias_vs_beta,coverage_vs_beta,bias_distributions} ...
visualization.py: error: unrecognized arguments: --plot

- python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png -> rc=2

usage: visualization.py [-h]
                        {bias_vs_beta,coverage_vs_beta,bias_distributions} ...
visualization.py: error: unrecognized arguments: --plot

- python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png -> rc=2

usage: visualization.py [-h]
                        {bias_vs_beta,coverage_vs_beta,bias_distributions} ...
visualization.py: error: unrecognized arguments: --plot

- python code/analysis.py --verify-sensitivity --input data/results/sensitivity_analysis.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis.py", line 12, in <module>
    from analysis.pipeline import run_imputation_and_estimation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/pipeline.py", line 16, in <module>
    from .causal_estimation import estimate_ate_ipw, estimate_ate_psm
ImportError: cannot import name 'estimate_ate_ipw' from 'analysis.causal_estimation' (/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/causal_estimation.py)


## Declared deliverables still missing

- data/results/power_analysis.json
- data/results/sensitivity_analysis.json
- data/results/sensitivity_analysis_dataset.csv
- data/results/simulation_summary.csv
- data/results/statistical_test_results.json
- data/results/us1_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/simulation_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregation.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/plot_bias.py` — NOT invoked by the run-book
    - `code/analysis/plot_coverage.py` — NOT invoked by the run-book
    - `code/analysis/plot_distributions.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/analysis/schemas.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/simulation_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/statistical_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/schemas.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/results/statistical_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/us1_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/run_simulation.py` — IS a run-book command
    - `code/simulation/verify_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us1_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
