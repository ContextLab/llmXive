# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_pipeline.py --stage train-static-model --seed 123

## Failing / missing run-book commands

- python src/cli/run_pipeline.py --stage train-static-model --seed 123 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-870-llmxive-follow-up-extending-ace-ego-0-un/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-870-llmxive-follow-up-extending-ace-ego-0-un/src/cli/run_pipeline.py': [Errno 2] No such file or directory

