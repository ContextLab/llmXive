# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity; 3 command(s) failed: python code/validate_trajectories.py  --input data/raw/trajectories.json (rc=1); python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42 (rc=1); python code/analyze_results.py  --input data/logs/simulation_results.csv  --output-dir results (rc=1)

## Failing / missing run-book commands

- python code/validate_trajectories.py  --input data/raw/trajectories.json -> rc=1
-10-15 04:28:40,575 - ERROR -   - Trajectory 0: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 1: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 2: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 3: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 4: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 5: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 6: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 7: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 8: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   - Trajectory 9: Entropy mismatch (target=2.0000, measured=0.0000, diff=2.0000)
2026-10-15 04:28:40,575 - ERROR -   ... and 490 more.

- python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42 -> rc=1

2026-10-15 04:28:40,619 - INFO - Starting simulation (seed=42)
2026-10-15 04:28:40,620 - INFO - Loading trajectories from data/raw/trajectories.json
2026-10-15 04:28:40,629 - INFO - Loaded 500 trajectories
2026-10-15 04:28:40,649 - INFO - Simulation completed in 0.02 seconds
2026-10-15 04:28:40,650 - INFO - Wrote 5000 records to data/logs/simulation_results.csv
2026-10-15 04:28:40,650 - INFO - Memory usage OK: 0.15 GB
2026-10-15 04:28:40,650 - INFO - Output file size: 241085 bytes
2026-10-15 04:28:40,651 - ERROR - Line count mismatch: expected 5001, got 5000

- python code/analyze_results.py  --input data/logs/simulation_results.csv  --output-dir results -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py", line 11, in <module>
    from patsy.dmatrix import dmatrix
ModuleNotFoundError: No module named 'patsy.dmatrix'

- python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory

