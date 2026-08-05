# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python scripts/verify_outputs.py

## Failing / missing run-book commands

- python scripts/verify_outputs.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-185-predicting-protein-protein-interactions-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-185-predicting-protein-protein-interactions-/scripts/verify_outputs.py': [Errno 2] No such file or directory
