# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.cli main ingest --config config.yaml (rc=1); python -m src.cli main resample --config config.yaml (rc=1); python -m src.cli main meta --config config.yaml (rc=1)

## Failing / missing run-book commands

- python -m src.cli main ingest --config config.yaml -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-372-assessing-the-sensitivity-of-regression-/code/.venv/bin/python: No module named src.cli
- python -m src.cli main resample --config config.yaml -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-372-assessing-the-sensitivity-of-regression-/code/.venv/bin/python: No module named src.cli
- python -m src.cli main meta --config config.yaml -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-372-assessing-the-sensitivity-of-regression-/code/.venv/bin/python: No module named src.cli
- python -m src.cli main report --config config.yaml -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-372-assessing-the-sensitivity-of-regression-/code/.venv/bin/python: No module named src.cli
