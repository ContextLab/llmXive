# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_trajectories.py  --num-trajectories <sufficient-number-of-trajectories>  --output data/raw/trajectories.jsonl  --seed 42`
  - script usage: `generate_trajectories.py [-h] [--num-trajectories NUM_TRAJECTORIES]`
  - argparse error: `generate_trajectories.py: error: argument --num-trajectories: invalid int value: '<sufficient-number-of-trajectories>'`
- run-book command: `python code/validate_simulation.py  --input data/logs/simulation_results.csv`
  - script usage: `validate_simulation.py [-h] [--seed SEED]`
  - argparse error: `validate_simulation.py: error: unrecognized arguments: --input data/logs/simulation_results.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.jsonl  --output-dir results/sensitivity; 4 command(s) failed: python code/generate_trajectories.py  --num-trajectories <sufficient-number-of-trajectories>  --output data/raw/trajectories.jsonl  --seed 42 (rc=2); python code/validate_trajectories.py  --input data/raw/trajectories.jsonl (rc=1); python code/validate_simulation.py  --input data/logs/simulation_results.csv (rc=2)

## Failing / missing run-book commands

- python code/generate_trajectories.py  --num-trajectories <sufficient-number-of-trajectories>  --output data/raw/trajectories.jsonl  --seed 42 -> rc=2

usage: generate_trajectories.py [-h] [--num-trajectories NUM_TRAJECTORIES]
                                [--seed SEED] [--output OUTPUT]
generate_trajectories.py: error: argument --num-trajectories: invalid int value: '<sufficient-number-of-trajectories>'

- python code/validate_trajectories.py  --input data/raw/trajectories.jsonl -> rc=1
47,043 - ERROR - Validation failed: 327/500 passed, 173 failed.
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 0: Entropy mismatch (target=1.5000, actual=1.6302, diff=0.1302)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 3: Entropy mismatch (target=1.5000, actual=1.6452, diff=0.1452)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 6: Entropy mismatch (target=1.5000, actual=1.6365, diff=0.1365)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 9: Entropy mismatch (target=1.5000, actual=1.5813, diff=0.0813)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 12: Entropy mismatch (target=1.5000, actual=1.5759, diff=0.0759)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 15: Entropy mismatch (target=1.5000, actual=1.6287, diff=0.1287)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 18: Entropy mismatch (target=1.5000, actual=1.5745, diff=0.0745)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 21: Entropy mismatch (target=1.5000, actual=1.5715, diff=0.0715)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 24: Entropy mismatch (target=1.5000, actual=1.6355, diff=0.1355)
2026-10-15 18:39:47,044 - ERROR -   - Trajectory 27: Entropy mismatch (target=1.5000, actual=1.6286, diff=0.1286)

- python code/validate_simulation.py  --input data/logs/simulation_results.csv -> rc=2

usage: validate_simulation.py [-h] [--seed SEED]
validate_simulation.py: error: unrecognized arguments: --input data/logs/simulation_results.csv

- python code/analyze_results.py  --input data/logs/simulation_results.csv  --output-dir results -> rc=1
870981665342372, horizon=3): 1 samples (min required: 10)
  Bin (density=0.9870981665342372, horizon=4): 1 samples (min required: 10)
  Bin (density=0.9870981665342372, horizon=5): 1 samples (min required: 10)
  Bin (density=0.9870981665342372, horizon=6): 1 samples (min required: 10)
  Bin (density=0.9870981665342372, horizon=7): 1 samples (min required: 10)
  Bin (density=0.9870981665342372, horizon=8): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=1): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=2): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=3): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=4): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=5): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=6): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=7): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=8): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=9): 1 samples (min required: 10)
  Bin (density=0.9871341955862344, horizon=10): 1 samples (min required: 10)


- python code/sensitivity.py  --input data/raw/trajectories.jsonl  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory

