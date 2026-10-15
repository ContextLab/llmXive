# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity; 1 command(s) failed: python code/validate_trajectories.py  --input data/raw/trajectories.json (rc=1)

## Failing / missing run-book commands

- python code/validate_trajectories.py  --input data/raw/trajectories.json -> rc=1
rajectories from data/raw/trajectories.json
2026-10-15 09:21:10,541 - ERROR - Validation failed: 0/500 passed, 500 failed.
2026-10-15 09:21:10,541 - ERROR - Details of failed trajectories (first 10 shown):
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 0: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 1: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 2: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 3: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 4: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 5: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 6: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 7: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 8: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   - Trajectory 9: Missing required fields: ['is_last_turn']
2026-10-15 09:21:10,541 - ERROR -   ... and 490 more.

- python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory

