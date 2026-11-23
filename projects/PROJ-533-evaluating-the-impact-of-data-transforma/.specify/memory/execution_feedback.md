# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.main --stage all (rc=-1); python -m code.main --stage all --resume --run-id your_run_id (rc=-1)

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=-1
2026-10-21 20:38:30,599 - pipeline - INFO - Executing full pipeline: download -> checksum


[TIMEOUT after 120s]
- python -m code.main --stage all --resume --run-id your_run_id -> rc=-1
2026-10-21 20:40:30,717 - pipeline - INFO - Attempting to resume from checkpoint: your_run_id
2026-10-21 20:40:30,717 - pipeline - WARNING - No checkpoint found for run_id. Starting from scratch.
2026-10-21 20:40:30,717 - pipeline - INFO - Executing full pipeline: download -> checksum


[TIMEOUT after 120s]
