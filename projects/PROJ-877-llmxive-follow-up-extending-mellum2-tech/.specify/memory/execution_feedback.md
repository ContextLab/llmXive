# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m code.main --phase all --sample small (rc=1)

## Failing / missing run-book commands

- python -m code.main --phase all --sample small -> rc=1
2026-10-14 17:35:21,680 - llmXive.main - Failed to load DAG: Invalid DAG format: missing 'tasks' key


