# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_trajectories.py  --num-trajectories <sufficient-number-of-trajectories>  --output data/raw/trajectories.jsonl  --seed 42`
  - script usage: `generate_trajectories.py [-h] [--count COUNT] [--seed SEED]`
  - argparse error: `generate_trajectories.py: error: unrecognized arguments: --num-trajectories <sufficient-number-of-trajectories>`
- run-book command: `python code/validate_simulation.py  --input data/logs/simulation_results.csv`
  - script usage: `validate_simulation.py [-h] [--seed SEED]`
  - argparse error: `validate_simulation.py: error: unrecognized arguments: --input data/logs/simulation_results.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.jsonl  --output-dir results/sensitivity; 4 command(s) failed: python code/generate_trajectories.py  --num-trajectories <sufficient-number-of-trajectories>  --output data/raw/trajectories.jsonl  --seed 42 (rc=2); python code/validate_trajectories.py  --input data/raw/trajectories.jsonl (rc=1); python code/simulate_agent.py  --input data/raw/trajectories.jsonl  --output data/logs/simulation_results.csv  --seed 42 (rc=1)

## Failing / missing run-book commands

- python code/generate_trajectories.py  --num-trajectories <sufficient-number-of-trajectories>  --output data/raw/trajectories.jsonl  --seed 42 -> rc=2

usage: generate_trajectories.py [-h] [--count COUNT] [--seed SEED]
                                [--output OUTPUT]
generate_trajectories.py: error: unrecognized arguments: --num-trajectories <sufficient-number-of-trajectories>

- python code/validate_trajectories.py  --input data/raw/trajectories.jsonl -> rc=1

2026-10-15 18:38:07,857 - ERROR - Invalid JSON in trajectory file: Extra data: line 2 column 1 (char 4645)

- python code/simulate_agent.py  --input data/raw/trajectories.jsonl  --output data/logs/simulation_results.csv  --seed 42 -> rc=1

2026-10-15 18:38:07,904 - INFO - Starting simulation (seed=42)
2026-10-15 18:38:07,904 - INFO - Loading trajectories from data/raw/trajectories.jsonl
2026-10-15 18:38:07,906 - ERROR - Data Flow Violation: Invalid JSON in trajectory file: Extra data: line 2 column 1 (char 4645)

- python code/validate_simulation.py  --input data/logs/simulation_results.csv -> rc=2

usage: validate_simulation.py [-h] [--seed SEED]
validate_simulation.py: error: unrecognized arguments: --input data/logs/simulation_results.csv

- python code/sensitivity.py  --input data/raw/trajectories.jsonl  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory

