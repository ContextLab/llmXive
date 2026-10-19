# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/validate.py`
  - script usage: `validate.py [-h] --input INPUT [--schema SCHEMA]`
  - argparse error: `validate.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python code/src/data/clean.py (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1
ub.errors.RemoteEntryNotFoundError: 404 Client Error. (Request ID: Root=1-6ad5b498-2e7e6fba011ffce5675bf00c;a364afc0-7846-460a-a670-9bc44a1ae633)

Entry Not Found for url: https://huggingface.co/datasets/chrisvoncsefalvay/vaers-outcomes/resolve/main/vaers_2020_2023.parquet.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 194, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 187, in main
    fetch_vaers_data()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 157, in fetch_vaers_data
    parquet_path = download_parquet()
                   ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 98, in download_parquet
    raise RuntimeError(
RuntimeError: Unable to download chrisvoncsefalvay/vaers-outcomes:vaers_2020_2023.parquet

- python src/data/validate.py -> rc=2

usage: validate.py [-h] --input INPUT [--schema SCHEMA]
validate.py: error: the following arguments are required: --input

- python code/src/data/clean.py -> rc=1

2026-10-19 06:11:37,574 - clean - INFO - Starting data cleaning process
2026-10-19 06:11:37,574 - clean - ERROR - No VAERS CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/code/data/raw

- python src/main.py -> rc=1
2026-10-19 06:11:38,326 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-19 06:11:38,416 - matplotlib.font_manager - INFO - generated new fontManager
2026-10-19 06:11:38,684 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


