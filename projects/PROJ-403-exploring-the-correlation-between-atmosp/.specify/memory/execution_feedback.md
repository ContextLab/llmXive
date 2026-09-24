# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.cli.run_analysis --full (rc=2); python -m src.cli.run_analysis --phase 6 # executes only phase 6 (sensitivity) (rc=2)

## Failing / missing run-book commands

- python -m src.cli.run_analysis --full -> rc=2
    Usage: python -m src.cli.run_analysis [OPTIONS]
Try 'python -m src.cli.run_analysis --help' for help.

Error: No such option '--full'.
- python -m src.cli.run_analysis --phase 6 # executes only phase 6 (sensitivity) -> rc=2
    Usage: python -m src.cli.run_analysis [OPTIONS]
Try 'python -m src.cli.run_analysis --help' for help.

Error: No such option '--phase'. Did you mean '--help'?
