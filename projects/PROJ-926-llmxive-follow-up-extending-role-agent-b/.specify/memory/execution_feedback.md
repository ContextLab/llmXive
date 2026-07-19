# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/analysis/statistical_tests.py --input data/derived/baseline_scores.jsonl,data/derived/degraded_scores.jsonl,data/derived/intervention_scores.jsonl --output data/derived/stats.csv; 6 command(s) failed: python code/src/sim/trajectory_generator.py --n 500 --condition baseline --output data/raw/baseline_trajectories.jsonl (rc=1); python code/src/sim/trajectory_generator.py --n 500 --condition degraded --output data/raw/degraded_trajectories.jsonl (rc=1); python code/src/sim/trajectory_generator.py --n 500 --condition intervention --output data/raw/intervention_trajectories.jsonl (rc=1); 2 declared deliverable(s) absent: data/raw/baseline_failures.json; data/raw/excluded_log.json

## Failing / missing run-book commands

- python code/src/sim/trajectory_generator.py --n 500 --condition baseline --output data/raw/baseline_trajectories.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/code/src/sim/trajectory_generator.py", line 16, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python code/src/sim/trajectory_generator.py --n 500 --condition degraded --output data/raw/degraded_trajectories.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/code/src/sim/trajectory_generator.py", line 16, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python code/src/sim/trajectory_generator.py --n 500 --condition intervention --output data/raw/intervention_trajectories.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/code/src/sim/trajectory_generator.py", line 16, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/sim/validation.py --input data/raw/baseline_trajectories.jsonl --output data/derived/baseline_validated.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/validation.py", line 12, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/sim/validation.py --input data/raw/degraded_trajectories.jsonl --output data/derived/degraded_validated.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/validation.py", line 12, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/sim/validation.py --input data/raw/intervention_trajectories.jsonl --output data/derived/intervention_validated.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/validation.py", line 12, in <module>
    from src.sim.alfworld_runner import run_episode
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/sim/alfworld_runner.py", line 14, in <module>
    import alfworld
ModuleNotFoundError: No module named 'alfworld'
- python src/analysis/statistical_tests.py --input data/derived/baseline_scores.jsonl,data/derived/degraded_scores.jsonl,data/derived/intervention_scores.jsonl --output data/derived/stats.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-926-llmxive-follow-up-extending-role-agent-b/src/analysis/statistical_tests.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/raw/baseline_failures.json
- data/raw/excluded_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/baseline_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/sim/trajectory_generator.py` — IS a run-book command
    - `code/tests/integration/test_baseline_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/baseline_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/excluded_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/sim/trajectory_generator.py` — IS a run-book command
    - `code/src/sim/exclusion_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/excluded_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
