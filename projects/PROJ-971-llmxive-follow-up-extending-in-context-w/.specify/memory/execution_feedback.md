# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash -c "source quickstart.sh && ./run_minimal.sh"

## Failing / missing run-book commands

- bash -c "source quickstart.sh && ./run_minimal.sh" -> rc=-1

shell script must be an existing project-local .sh file
