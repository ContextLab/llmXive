# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/src/run_pipeline.py --seed 42 --max-species 100 --output-dir outputs/ (rc=1); python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml (rc=1); python -m llmxive_toolkit.validate_contracts  --data "$f"  --schema contracts/model_output.schema.yaml (rc=1); 1 declared deliverable(s) absent: data/processed/clean.parquet

## Failing / missing run-book commands

- python code/src/run_pipeline.py --seed 42 --max-species 100 --output-dir outputs/ -> rc=1
/preprocess.py", line 239, in load_and_preprocess
    df.to_parquet(out_path, index=False)
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/util/_decorators.py", line 333, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 3113, in to_parquet
    return to_parquet(
           ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 476, in to_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 67, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python -m llmxive_toolkit.validate_contracts  --data "$f"  --schema contracts/model_output.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python code/src/run_pipeline.py --seed 42 --use-placeholder --output-dir outputs_demo/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 112, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 67, in main
    raise RuntimeError(
RuntimeError: Placeholder data is not permitted for T002. The pipeline requires real datasets from MetaboLights, PMN, and HPID.


## Declared deliverables still missing

- data/processed/clean.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clean.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/correlation_analysis.py` — NOT invoked by the run-book
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/src/run_pipeline.py` — IS a run-book command
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clean.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
