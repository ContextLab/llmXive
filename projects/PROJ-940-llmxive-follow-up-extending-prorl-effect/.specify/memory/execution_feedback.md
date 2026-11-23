# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python main.py --download-only; python main.py --seed 42 --path-length 5 --alpha 0.1 --beam-width 50 --k 10; python main.py --sweep-thresholds 0.01,0.05,0.1

## Failing / missing run-book commands

- python main.py --download-only -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/main.py': [Errno 2] No such file or directory

- python main.py --seed 42 --path-length 5 --alpha 0.1 --beam-width 50 --k 10 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/main.py': [Errno 2] No such file or directory

- python main.py --sweep-thresholds 0.01,0.05,0.1 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/main.py': [Errno 2] No such file or directory

