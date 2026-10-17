# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/data_ingestion.py (rc=1); python code/preprocessing.py (rc=1); python code/visualization.py (rc=1)

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/data_ingestion.py", line 238, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/data_ingestion.py", line 187, in main
    config = get_config()
             ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/data_ingestion.py", line 19, in get_config
    return yaml.safe_load(f)
           ^^^^
NameError: name 'yaml' is not defined

- python code/preprocessing.py -> rc=1
2026-10-17 15:31:39,391 - llmXive - INFO - Starting preprocessing pipeline (T016)...
2026-10-17 15:31:39,392 - llmXive - ERROR - Preprocessing pipeline failed: Input file data/processed/merged_root_soil.csv not found. Run data_ingestion.py (T015) first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/preprocessing.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/preprocessing.py", line 163, in main
    raise FileNotFoundError(
FileNotFoundError: Input file data/processed/merged_root_soil.csv not found. Run data_ingestion.py (T015) first.

- python code/visualization.py -> rc=1

ERROR:root:Processed data not found at data/raw/processed/cleaned_data.csv. Run T015 first.

