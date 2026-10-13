# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python main.py  --variant grpo  --env alfworld  --seed 42  --max-steps 1000  --output-dir data/processed/grpo-alfworld; python main.py  --variant baseline  --env alfworld  --seed 42  --max-steps 1000  --output-dir data/processed/baseline-alfworld; python main.py  --variant student-only  --env alfworld  --seed 42  --max-steps 1000  --output-dir data/processed/student-only-alfworld

## Failing / missing run-book commands

- python main.py  --variant grpo  --env alfworld  --seed 42  --max-steps 1000  --output-dir data/processed/grpo-alfworld -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/main.py': [Errno 2] No such file or directory

- python main.py  --variant baseline  --env alfworld  --seed 42  --max-steps 1000  --output-dir data/processed/baseline-alfworld -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/main.py': [Errno 2] No such file or directory

- python main.py  --variant student-only  --env alfworld  --seed 42  --max-steps 1000  --output-dir data/processed/student-only-alfworld -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/main.py': [Errno 2] No such file or directory

- python main.py  --variant student-only-replay  --env alfworld  --input-trajectories data/processed/baseline-alfworld/trajectories.jsonl  --output-dir data/processed/student-only-replay-alfworld -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/main.py': [Errno 2] No such file or directory

- python metrics/statistical_test.py  --grpo-dir data/processed/grpo-alfworld  --baseline-dir data/processed/baseline-alfworld  --student-only-dir data/processed/student-only-alfworld  --replay-dir data/processed/student-only-replay-alfworld  --output data/processed/comparison_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-825-llmxive-follow-up-extending-self-distill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-825-llmxive-follow-up-extending-self-distill/metrics/statistical_test.py': [Errno 2] No such file or directory

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
