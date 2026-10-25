# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/validate.py`
  - script usage: `validate.py [-h] --input INPUT [--schema SCHEMA]`
  - argparse error: `validate.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python src/data/validate.py (rc=2); python src/data/clean.py (rc=1); python src/main.py (rc=1)

## Failing / missing run-book commands

- python src/data/validate.py -> rc=2

usage: validate.py [-h] --input INPUT [--schema SCHEMA]
validate.py: error: the following arguments are required: --input

- python src/data/clean.py -> rc=1
icly-availab/src/data/clean.py", line 336, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/clean.py", line 313, in main
    data = process_data(input_files, mapping_df, logger)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/clean.py", line 196, in process_data
    processed_df = process_chunk(df, mapping_df, logger)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/clean.py", line 126, in process_chunk
    chunk = chunk[chunk["VAX_TYPE"].notna() & (chunk["VAX_TYPE"] != "")]
                  ~~~~~^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 4102, in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/indexes/base.py", line 3812, in get_loc
    raise KeyError(key) from err
KeyError: 'VAX_TYPE'

- python src/main.py -> rc=1
2026-10-25 17:11:25,025 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-25 17:11:25,054 - matplotlib.font_manager - INFO - generated new fontManager
2026-10-25 17:11:25,386 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


