# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/cli/run_pipeline.py --stage download (rc=1); python code/cli/run_pipeline.py --stage validate (rc=1); 1 declared deliverable(s) absent: data/logs/schema_validation.json

## Failing / missing run-book commands

- python code/cli/run_pipeline.py --stage download -> rc=1
ng-corrosion-potential-from-comp/logs/download_summary.json
2026-11-11 09:22:56,708 INFO code.data.download_nist: Wrote download log to /home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/logs/download.log
2026-11-11 09:22:56,708 ERROR code.data.download_nist: Insufficient records after download: 0 (minimum required: 500).
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 88, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 81, in main
    stage_func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 28, in run_download_stage
    download_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/data/download_nist.py", line 277, in main
    raise DataInsufficientError(message)
code.utils.exceptions.DataInsufficientError: Insufficient records after download: 0 (minimum required: 500).

- python code/cli/run_pipeline.py --stage validate -> rc=1
 "__main__", "level": "ERROR", "message": "Stage 'validate' failed: No CSV files found in the raw data directory."}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 88, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 81, in main
    stage_func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 33, in run_validate_stage
    validate_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/data/validate_raw.py", line 163, in main
    df = load_raw_dataset(csv_files)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/data/validate_raw.py", line 62, in load_raw_dataset
    raise SchemaMismatchError("No CSV files found in the raw data directory.")
code.utils.exceptions.SchemaMismatchError: No CSV files found in the raw data directory.


## Declared deliverables still missing

- data/logs/schema_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/schema_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_raw.py` — NOT invoked by the run-book
    - `code/setup_schema_contracts.py` — NOT invoked by the run-book
    - `code/utils/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/schema_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
