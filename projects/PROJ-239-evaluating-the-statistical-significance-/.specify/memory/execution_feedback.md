# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/simulation_runner.py`
  - script usage: `simulation_runner.py [-h] [--icc ICC] [--iterations ITERATIONS]`
  - argparse error: `simulation_runner.py: error: unrecognized arguments: icc iterations seed n_clusters n_obs_per_cluster icc_range icc_step alpha alpha_list n_permutations output_baseline output_robust mode`
- run-book command: `python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100`
  - script usage: `simulation_runner.py [-h] [--icc ICC] [--iterations ITERATIONS]`
  - argparse error: `simulation_runner.py: error: unrecognized arguments: icc iterations seed n_clusters n_obs_per_cluster icc_range icc_step alpha alpha_list n_permutations output_baseline output_robust mode`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/simulation_runner.py (rc=2); python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 (rc=2); 4 declared deliverable(s) absent: data/derived/baseline_results.csv; data/derived/final_report.csv; data/derived/robustResults.csv

## Failing / missing run-book commands

- python code/simulation_runner.py -> rc=2
    usage: simulation_runner.py [-h] [--icc ICC] [--iterations ITERATIONS]
                            [--seed SEED] [--n-clusters N_CLUSTERS]
                            [--n-obs-per-cluster N_OBS_PER_CLUSTER]
                            [--icc-range ICC_RANGE] [--icc-step ICC_STEP]
                            [--alpha ALPHA] [--alpha-list ALPHA_LIST]
                            [--n-permutations N_PERMUTATIONS]
                            [--output-baseline OUTPUT_BASELINE]
                            [--output-robust OUTPUT_ROBUST]
simulation_runner.py: error: unrecognized arguments: icc iterations seed n_clusters n_obs_per_cluster icc_range icc_step alpha alpha_list n_permutations output_baseline output_robust mode
- python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 -> rc=2
    usage: simulation_runner.py [-h] [--icc ICC] [--iterations ITERATIONS]
                            [--seed SEED] [--n-clusters N_CLUSTERS]
                            [--n-obs-per-cluster N_OBS_PER_CLUSTER]
                            [--icc-range ICC_RANGE] [--icc-step ICC_STEP]
                            [--alpha ALPHA] [--alpha-list ALPHA_LIST]
                            [--n-permutations N_PERMUTATIONS]
                            [--output-baseline OUTPUT_BASELINE]
                            [--output-robust OUTPUT_ROBUST]
simulation_runner.py: error: unrecognized arguments: icc iterations seed n_clusters n_obs_per_cluster icc_range icc_step alpha alpha_list n_permutations output_baseline output_robust mode

## Declared deliverables still missing

- data/derived/baseline_results.csv
- data/derived/final_report.csv
- data/derived/robustResults.csv
- data/derived/synthetic_cluster_structure.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `parse_cli_args` — defined in `code/config.py`; called 4 way(s):

- code/config.py: 1. parse_cli_args() - Returns config with defaults
- code/config.py: 2. parse_cli_args(args) - Parses args and returns new config
- code/config.py: 3. parse_cli_args(args, cfg) - Parses args and updates existing config
- code/simulation_runner.py: cfg = parse_cli_args(args, cfg)

Make `parse_cli_args` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/run_simulation_baseline.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/simulation_runner.py` — IS a run-book command
    - `code/scripts/merge_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/final_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/merge_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/final_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/robustResults.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/run_simulation_robust.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/simulation_runner.py` — IS a run-book command
    - `code/scripts/merge_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/robustResults.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/synthetic_cluster_structure.csv` is declared but was NOT written. Scripts referencing it:
    - `code/synthetic_cluster_params.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/synthetic_cluster_structure.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
