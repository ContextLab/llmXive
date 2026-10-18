# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.cli.run_fidelity  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 (rc=1); python -m pytest -q tests/contract (rc=4)

## Failing / missing run-book commands

- python -m src.cli.run_fidelity  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/bin/python: Error while finding module specification for 'src.cli.run_fidelity' (ModuleNotFoundError: No module named 'src.cli')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


