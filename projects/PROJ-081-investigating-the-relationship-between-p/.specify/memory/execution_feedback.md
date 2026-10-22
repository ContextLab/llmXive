# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/run_pipeline.py  --seed 42  --max-species 100  --output-dir outputs/; python src/run_pipeline.py  --seed 42  --use-placeholder  --output-dir outputs_demo/; 2 command(s) failed: python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml (rc=1); python -m llmxive_toolkit.validate_contracts  --data "$result_file"  --schema contracts/model_output.schema.yaml (rc=1); 1 declared deliverable(s) absent: data/processed/clean.parquet

## Failing / missing run-book commands

- python src/run_pipeline.py  --seed 42  --max-species 100  --output-dir outputs/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/src/run_pipeline.py': [Errno 2] No such file or directory

- python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python -m llmxive_toolkit.validate_contracts  --data "$result_file"  --schema contracts/model_output.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python src/run_pipeline.py  --seed 42  --use-placeholder  --output-dir outputs_demo/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/src/run_pipeline.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/clean.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clean.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/correlation_analysis.py` — NOT invoked by the run-book
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clean.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
