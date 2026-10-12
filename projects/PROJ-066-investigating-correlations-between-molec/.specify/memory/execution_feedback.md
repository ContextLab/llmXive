# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/preprocess.py --max-samples '<variable>'`
  - script usage: `preprocess.py [-h] [--max-samples MAX_SAMPLES]`
  - argparse error: `preprocess.py: error: argument --max-samples: invalid int value: '<variable>'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/data/download.py --target bioavailability,permeability,clearance (rc=-1); python code/data/preprocess.py --max-samples '<variable>' (rc=2); python code/utils/update_state.py --stage preprocess (rc=1)

## Failing / missing run-book commands

- python code/data/download.py --target bioavailability,permeability,clearance -> rc=-1
{"timestamp": "2026-10-12T06:38:40.484344", "level": "INFO", "module": "logging", "message": "[T009] Starting ChEMBL 33 data acquisition - Status: in_progress"}
{"timestamp": "2026-10-12T06:38:40.484419", "level": "INFO", "module": "download", "message": "Fetching ChEMBL activities for standard types: ['ORAL BIOAVAILABILITY', 'ORAL BIOAVAILABILITY %', 'F', 'BIOAVAILABILITY', 'PAPP', 'PAPP (10-6 CM/S)', 'PERMEABILITY', 'CACO2 PERMEABILITY', 'CLEARANCE', 'CLEARANCE ML/MIN/KG', 'CLEARANCE ML/MIN', 'HEPATIC CLEARANCE'] (max 20000 records)"}
{"timestamp": "2026-10-12T06:38:46.511562", "level": "INFO", "module": "download", "message": "ChEMBL reports 32527 matching activities in total."}


[TIMEOUT after 120s]
- python code/data/preprocess.py --max-samples '<variable>' -> rc=2

usage: preprocess.py [-h] [--max-samples MAX_SAMPLES]
preprocess.py: error: argument --max-samples: invalid int value: '<variable>'

- python code/utils/update_state.py --stage preprocess -> rc=1
/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/--stage'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 190, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 185, in main
    update_state(DEFAULT_PROJECT_ID, artifacts)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 162, in update_state
    entry["hash"] = compute_file_hash(full_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 47, in compute_file_hash
    raise FileNotFoundError(f"File not found for hashing: {file_path}")
FileNotFoundError: File not found for hashing: /home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/--stage

- python code/models/train.py --target bioavailability --seed 42 -> rc=1
{"timestamp": "2026-10-12T06:40:41.250534", "level": "INFO", "module": "train", "message": "Starting Model Training Pipeline (T036 Refactor)"}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py", line 207, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py", line 177, in main
    df = load_processed_data(PROCESSED_DATA_PATH)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py", line 57, in load_processed_data
    raise FileNotFoundError(f"Processed data not found at {data_path}")
FileNotFoundError: Processed data not found at /home/runner/work/llmXive/llmXive/projects/data/processed/molecules_processed.csv

- python code/utils/update_state.py --stage train -> rc=1
/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/--stage'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 190, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 185, in main
    update_state(DEFAULT_PROJECT_ID, artifacts)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 162, in update_state
    entry["hash"] = compute_file_hash(full_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 47, in compute_file_hash
    raise FileNotFoundError(f"File not found for hashing: {file_path}")
FileNotFoundError: File not found for hashing: /home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/--stage

- python code/models/evaluate.py --model rf --target bioavailability -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py", line 239, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py", line 125, in main
    log_pipeline_step("START_EVALUATION")
TypeError: log_pipeline_step() missing 1 required positional argument: 'step_name'

- python code/utils/update_state.py --stage evaluate -> rc=1
/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/--stage'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 190, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 185, in main
    update_state(DEFAULT_PROJECT_ID, artifacts)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 162, in update_state
    entry["hash"] = compute_file_hash(full_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py", line 47, in compute_file_hash
    raise FileNotFoundError(f"File not found for hashing: {file_path}")
FileNotFoundError: File not found for hashing: /home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/--stage

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
