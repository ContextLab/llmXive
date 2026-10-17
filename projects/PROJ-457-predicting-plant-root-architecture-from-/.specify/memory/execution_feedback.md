# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data_ingestion.py (rc=1); python code/preprocessing.py (rc=1); python code/visualization.py (rc=1)

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1
2026-10-17 16:13:51,869 - llmXive - INFO - Starting T015c: Filter by Missing Nutrients

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/data_ingestion.py", line 239, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/data_ingestion.py", line 194, in main
    state_path = Path(config["ARTIFACTS_PATH"]) / "state.json"
                      ~~~~~~^^^^^^^^^^^^^^^^^^
KeyError: 'ARTIFACTS_PATH'

- python code/preprocessing.py -> rc=1
2026-10-17 16:13:52,688 - llmXive - INFO - Starting preprocessing pipeline (T016)...
2026-10-17 16:13:52,688 - llmXive - ERROR - Preprocessing pipeline failed: Input file data/processed/merged_root_soil.csv not found. Run data_ingestion.py (T015) first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/preprocessing.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/preprocessing.py", line 163, in main
    raise FileNotFoundError(
FileNotFoundError: Input file data/processed/merged_root_soil.csv not found. Run data_ingestion.py (T015) first.

- python code/visualization.py -> rc=1

ERROR:root:Processed data not found at data/raw/processed/cleaned_data.csv. Run T015 first.

- python -m pytest tests/contract/test_schemas.py -> rc=4

ERROR: /home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/pyproject.toml: Invalid value (at line 47, column 10)


