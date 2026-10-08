# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100`
  - script usage: `simulation_runner.py [-h] [--icc-range ICC_RANGE]`
  - argparse error: `simulation_runner.py: error: unrecognized arguments: --alpha 0.05`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 (rc=2); 1 declared deliverable(s) absent: data/derived/final_report.csv

## Failing / missing run-book commands

- python code/simulation_runner.py --icc 0.1 --alpha 0.05 --iterations 100 -> rc=2
    usage: simulation_runner.py [-h] [--icc-range ICC_RANGE]
                            [--iterations ITERATIONS] [--seed SEED]
                            [--cluster-mean CLUSTER_MEAN]
                            [--cluster-std CLUSTER_STD]
                            [--n-clusters N_CLUSTERS]
                            [--n-obs-per-cluster N_OBS_PER_CLUSTER]
                            [--n-permutations N_PERMUTATIONS]
                            [--output OUTPUT]
simulation_runner.py: error: unrecognized arguments: --alpha 0.05

## Declared deliverables still missing

- data/derived/final_report.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `parse_cli_args` — defined in `code/config.py`; called 10 way(s):

- code/config.py: cfg = parse_cli_args(cli_args, cfg)
- code/config.py: 1. parse_cli_args() -> Returns config with defaults (not supported directly, use load_config)
- code/config.py: 2. parse_cli_args(args) -> Parses args and returns new config
- code/config.py: 3. parse_cli_args(args, cfg) -> Parses args and updates existing config
- code/config.py: 4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)
- code/config.py: # Handle pattern 4: parse_cli_args(cfg) -> no CLI args, just defaults
- code/config.py: # Handle pattern 2: parse_cli_args(args) -> no cfg provided
- code/run_simulation_baseline.py: cfg = parse_cli_args(args, cfg)
- code/simulation_runner.py: cfg = parse_cli_args(args, cfg)
- code/scripts/merge_results.py: cfg = parse_cli_args(args, cfg)

Make `parse_cli_args` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/final_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/generate_final_report.py` — NOT invoked by the run-book
    - `code/scripts/merge_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/final_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
