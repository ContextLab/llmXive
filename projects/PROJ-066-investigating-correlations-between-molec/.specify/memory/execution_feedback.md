# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/data/preprocess.py --max-samples '<variable>' (rc=1); python code/models/train.py --target bioavailability --seed 42 (rc=1); python code/models/evaluate.py --model rf --target bioavailability (rc=1)

## Failing / missing run-book commands

- python code/data/preprocess.py --max-samples '<variable>' -> rc=1
cate_smiles - Status: in_progress"}
{"timestamp": "2026-10-14T21:38:31.200797", "level": "INFO", "module": "preprocess", "message": "Deduplication complete. Retained 0 unique SMILES."}
{"timestamp": "2026-10-14T21:38:31.200890", "level": "INFO", "module": "preprocess", "message": "Performing dataset sampling (T013)..."}
{"timestamp": "2026-10-14T21:38:31.200924", "level": "INFO", "module": "logging", "message": "[T013] sample_dataset - Status: in_progress"}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py", line 498, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py", line 488, in main
    df = sample_dataset(df, target_size=max_samples)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py", line 321, in sample_dataset
    raise DataInsufficiencyError("Data Insufficiency: Sample size < 100")
DataInsufficiencyError: Data Insufficiency: Sample size < 100

- python code/models/train.py --target bioavailability --seed 42 -> rc=1
{"timestamp": "2026-10-14T21:38:32.045250", "level": "INFO", "module": "train", "message": "Starting Model Training Pipeline (T036 Refactor)"}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py", line 207, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py", line 177, in main
    df = load_processed_data(PROCESSED_DATA_PATH)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py", line 57, in load_processed_data
    raise FileNotFoundError(f"Processed data not found at {data_path}")
FileNotFoundError: Processed data not found at /home/runner/work/llmXive/llmXive/projects/data/processed/molecules_processed.csv

- python code/models/evaluate.py --model rf --target bioavailability -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py", line 239, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py", line 125, in main
    log_pipeline_step("START_EVALUATION")
TypeError: log_pipeline_step() missing 1 required positional argument: 'step_name'

