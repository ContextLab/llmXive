# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py --target bioavailability,permeability,clearance`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data/download.py --target bioavailability,permeability,clearance (rc=1); python code/data/preprocess.py --max-samples '<variable>' (rc=1); python code/models/train.py --target bioavailability --seed 42 (rc=1)

## Failing / missing run-book commands

- python code/data/download.py --target bioavailability,permeability,clearance -> rc=1
", line 359, in ntransfercmd
    resp = self.sendcmd(cmd)
           ^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 281, in sendcmd
    return self.getresp()
           ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 254, in getresp
    raise error_perm(resp)
ftplib.error_perm: 550 Failed to open file.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/download.py", line 168, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/download.py", line 127, in main
    download_chembl_ftp(CHEMBL_FTP_HOST, CHEMBL_FPS_PATH, GZIPPED_TEMP_FILE)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/download.py", line 67, in download_chembl_ftp
    raise RuntimeError(f"Failed to download ChEMBL dataset from FTP: {e}")
RuntimeError: Failed to download ChEMBL dataset from FTP: 550 Failed to open file.

- python code/data/preprocess.py --max-samples '<variable>' -> rc=1
{"timestamp": "2026-10-12T06:23:57.141475", "level": "INFO", "module": "preprocess", "message": "Starting Preprocessing Pipeline (T036 Refactor)"}
{"timestamp": "2026-10-12T06:23:57.141568", "level": "ERROR", "module": "preprocess", "message": "Raw database not found at /home/runner/work/llmXive/llmXive/projects/data/raw/chembl_33.db. Please run T009 first."}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py", line 395, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py", line 362, in main
    raise FileNotFoundError(f"Raw database not found: {raw_db_path}")
FileNotFoundError: Raw database not found: /home/runner/work/llmXive/llmXive/projects/data/raw/chembl_33.db

- python code/models/train.py --target bioavailability --seed 42 -> rc=1
{"timestamp": "2026-10-12T06:23:57.762403", "level": "INFO", "module": "train", "message": "Starting Model Training Pipeline (T036 Refactor)"}

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

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
