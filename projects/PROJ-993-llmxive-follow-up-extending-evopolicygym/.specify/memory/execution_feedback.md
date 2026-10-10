# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --task discover`
  - script usage: `main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]`
  - argparse error: `main.py: error: argument command: invalid choice: 'discover' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')`
- run-book command: `python code/main.py --task validate_shifts`
  - script usage: `main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]`
  - argparse error: `main.py: error: argument command: invalid choice: 'validate_shifts' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')`
- run-book command: `python code/main.py --task evolve --seeds 5 --conditions baseline,counterfactual`
  - script usage: `main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]`
  - argparse error: `main.py: error: argument command: invalid choice: 'evolve' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')`
- run-book command: `python code/main.py --task analyze`
  - script usage: `main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]`
  - argparse error: `main.py: error: argument command: invalid choice: 'analyze' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --task discover (rc=2); python code/main.py --task validate_shifts (rc=2); python code/main.py --task evolve --seeds 5 --conditions baseline,counterfactual (rc=2); 6 declared deliverable(s) absent: data/discovered_envs.json; data/evolution_results.csv; data/masked_schema.json

## Failing / missing run-book commands

- python code/main.py --task discover -> rc=2

usage: main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]
               [--runs RUNS] [--envs ENVS [ENVS ...]]
               [--conditions CONDITIONS [CONDITIONS ...]]
               {run-shift-analysis,run-shift-validation,run-evolution,run-stats,run-full}
               ...
main.py: error: argument command: invalid choice: 'discover' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')

- python code/main.py --task validate_shifts -> rc=2

usage: main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]
               [--runs RUNS] [--envs ENVS [ENVS ...]]
               [--conditions CONDITIONS [CONDITIONS ...]]
               {run-shift-analysis,run-shift-validation,run-evolution,run-stats,run-full}
               ...
main.py: error: argument command: invalid choice: 'validate_shifts' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')

- python code/main.py --task evolve --seeds 5 --conditions baseline,counterfactual -> rc=2

usage: main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]
               [--runs RUNS] [--envs ENVS [ENVS ...]]
               [--conditions CONDITIONS [CONDITIONS ...]]
               {run-shift-analysis,run-shift-validation,run-evolution,run-stats,run-full}
               ...
main.py: error: argument command: invalid choice: 'evolve' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')

- python code/main.py --task analyze -> rc=2

usage: main.py [-h] [--config CONFIG] [--seeds SEEDS [SEEDS ...]]
               [--runs RUNS] [--envs ENVS [ENVS ...]]
               [--conditions CONDITIONS [CONDITIONS ...]]
               {run-shift-analysis,run-shift-validation,run-evolution,run-stats,run-full}
               ...
main.py: error: argument command: invalid choice: 'analyze' (choose from 'run-shift-analysis', 'run-shift-validation', 'run-evolution', 'run-stats', 'run-full')


## Declared deliverables still missing

- data/discovered_envs.json
- data/evolution_results.csv
- data/masked_schema.json
- data/run_state.json
- data/sensitivity_report.csv
- data/stats_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/discovered_envs.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/apply_shift_wrappers.py` — NOT invoked by the run-book
    - `code/analysis/run_shift_sensitivity.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/test_env_discovery.py` — NOT invoked by the run-book
    - `code/utils/env_discovery.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/discovered_envs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/evolution_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/agents/evolution_results_writer.py` — NOT invoked by the run-book
    - `code/agents/evolutionary_harness.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evolution_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/masked_schema.json` is declared but was NOT written. Scripts referencing it:
    - `code/explanation/generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/masked_schema.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/run_state.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/populate_sensitivity_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/run_state.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/populate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/run_shift_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_report_schema.py` — NOT invoked by the run-book
    - `code/analysis/shift_validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/stats_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/tests/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/stats_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
