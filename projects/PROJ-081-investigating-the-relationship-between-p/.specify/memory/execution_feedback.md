# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/src/run_pipeline.py --seed 42 --max-species 100 --output-dir outputs/ (rc=1); python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml (rc=1); python -m llmxive_toolkit.validate_contracts  --data "$f"  --schema contracts/model_output.schema.yaml (rc=1); 1 declared deliverable(s) absent: data/processed/clean.parquet

## Failing / missing run-book commands

- python code/src/run_pipeline.py --seed 42 --max-species 100 --output-dir outputs/ -> rc=1
ound for url: https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/MTBLS1/MTBLS1.tsv

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 124, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 88, in main
    df_metabolights = fetch_metabolights()
                      ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/fetch_data.py", line 150, in fetch_metabolights
    content = _fetch_with_backoff(METABOLIGHTS_URL)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/fetch_data.py", line 68, in _fetch_with_backoff
    raise RuntimeError(f"Failed to fetch {url}") from exc
RuntimeError: Failed to fetch https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/MTBLS1/MTBLS1.tsv

- python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python -m llmxive_toolkit.validate_contracts  --data "$f"  --schema contracts/model_output.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python code/src/run_pipeline.py --seed 42 --use-placeholder --output-dir outputs_demo/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 124, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 79, in main
    raise RuntimeError(
RuntimeError: Placeholder data is not permitted for T001. The pipeline requires real datasets from MetaboLights, PMN, and HPID.


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
