# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --task discover (rc=2); python code/main.py --task validate_shifts (rc=2); python code/main.py --task evolve --seeds 5 --conditions baseline,counterfactual (rc=2); 6 declared deliverable(s) absent: data/discovered_envs.json; data/evolution_results.csv; data/masked_schema.json

## Failing / missing run-book commands

- python code/main.py --task discover -> rc=2

usage: main.py [-h] [--seeds SEEDS [SEEDS ...]] [--runs RUNS]
               [--conditions CONDITIONS [CONDITIONS ...]]
               [--task {discover,validate_shifts,evolve,analyze}]
               (--check | --run-evolution | --run-full-pipeline)
main.py: error: one of the arguments --check --run-evolution --run-full-pipeline is required

- python code/main.py --task validate_shifts -> rc=2

usage: main.py [-h] [--seeds SEEDS [SEEDS ...]] [--runs RUNS]
               [--conditions CONDITIONS [CONDITIONS ...]]
               [--task {discover,validate_shifts,evolve,analyze}]
               (--check | --run-evolution | --run-full-pipeline)
main.py: error: one of the arguments --check --run-evolution --run-full-pipeline is required

- python code/main.py --task evolve --seeds 5 --conditions baseline,counterfactual -> rc=2

usage: main.py [-h] [--seeds SEEDS [SEEDS ...]] [--runs RUNS]
               [--conditions CONDITIONS [CONDITIONS ...]]
               [--task {discover,validate_shifts,evolve,analyze}]
               (--check | --run-evolution | --run-full-pipeline)
main.py: error: one of the arguments --check --run-evolution --run-full-pipeline is required

- python code/main.py --task analyze -> rc=2

usage: main.py [-h] [--seeds SEEDS [SEEDS ...]] [--runs RUNS]
               [--conditions CONDITIONS [CONDITIONS ...]]
               [--task {discover,validate_shifts,evolve,analyze}]
               (--check | --run-evolution | --run-full-pipeline)
main.py: error: one of the arguments --check --run-evolution --run-full-pipeline is required


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
    - `code/environments/registry_wrapper.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/test_env_discovery.py` — NOT invoked by the run-book
    - `code/utils/env_discovery.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/discovered_envs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/evolution_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/agents/evolution_results_writer.py` — NOT invoked by the run-book
    - `code/agents/evolutionary_harness.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
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
