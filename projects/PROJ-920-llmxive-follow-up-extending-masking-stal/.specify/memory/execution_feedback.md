# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_trajectories.py  --num-trajectories 500  --output data/raw/trajectories.json  --seed 42`
  - script usage: `generate_trajectories.py [-h] [--seed SEED] [--count COUNT]`
  - argparse error: `generate_trajectories.py: error: unrecognized arguments: --num-trajectories 500 --output data/raw/trajectories.json`
- run-book command: `python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42`
  - script usage: `simulate_agent.py [-h] [--seed SEED]`
  - argparse error: `simulate_agent.py: error: unrecognized arguments: --input data/raw/trajectories.json --output data/logs/simulation_results.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity; 4 command(s) failed: python code/generate_trajectories.py  --num-trajectories 500  --output data/raw/trajectories.json  --seed 42 (rc=2); python code/validate_trajectories.py  --input data/raw/trajectories.json (rc=1); python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42 (rc=2); 1 declared deliverable(s) absent: data/raw/trajectories.json

## Failing / missing run-book commands

- python code/generate_trajectories.py  --num-trajectories 500  --output data/raw/trajectories.json  --seed 42 -> rc=2

usage: generate_trajectories.py [-h] [--seed SEED] [--count COUNT]
generate_trajectories.py: error: unrecognized arguments: --num-trajectories 500 --output data/raw/trajectories.json

- python code/validate_trajectories.py  --input data/raw/trajectories.json -> rc=1

2026-10-15 04:16:48,085 - INFO - Starting trajectory validation...
2026-10-15 04:16:48,085 - ERROR - Data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/data/raw/trajectories.json
2026-10-15 04:16:48,085 - ERROR - Run generate_trajectories.py (T011) first.

- python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42 -> rc=2

usage: simulate_agent.py [-h] [--seed SEED]
simulate_agent.py: error: unrecognized arguments: --input data/raw/trajectories.json --output data/logs/simulation_results.csv

- python code/analyze_results.py  --input data/logs/simulation_results.csv  --output-dir results -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py", line 11, in <module>
    from patsy.dmatrix import dmatrix
ModuleNotFoundError: No module named 'patsy.dmatrix'

- python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/trajectories.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/trajectories.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_trajectories.py` — IS a run-book command
    - `code/simulate_agent.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate_trajectories.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/trajectories.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
