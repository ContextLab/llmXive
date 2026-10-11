# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipelines.run_all  --max_tasks 200  --penalty_threshold 2.0  --seed 42 (rc=1); python -m pytest -q tests/contract (rc=4)

## Failing / missing run-book commands

- python -m src.pipelines.run_all  --max_tasks 200  --penalty_threshold 2.0  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-936-llmxive-follow-up-extending-a-matter-of/bin/python: Error while finding module specification for 'src.pipelines.run_all' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


