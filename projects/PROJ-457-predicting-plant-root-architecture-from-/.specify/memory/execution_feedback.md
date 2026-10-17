# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/aizenSosuke.parquet, data/raw/blanchon.parquet, data/raw/joaosanches.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/aizenSosuke.parquet, data/raw/blanchon.parquet, data/raw/joaosanches.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/ingestion.py (rc=1); python code/preprocessing.py (rc=1); python code/visualization.py (rc=1); 1 declared deliverable(s) absent: data/raw/merged_dataset.parquet

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
ack (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/ingestion.py", line 279, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/ingestion.py", line 214, in main
    df, source_file = download_merged_dataset(raw_dir, logger)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/ingestion.py", line 120, in download_merged_dataset
    raise RuntimeError(
RuntimeError: Could not fetch any verified merged dataset (3 URLs tried). Last error: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python code/preprocessing.py -> rc=1
2026-10-17 18:06:41,587 - llmXive - INFO - Starting preprocessing pipeline (T016)...
2026-10-17 18:06:41,588 - llmXive - ERROR - Preprocessing pipeline failed: Input file data/processed/merged_root_soil.csv not found. Run data_ingestion.py (T015) first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/preprocessing.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-457-predicting-plant-root-architecture-from-/code/preprocessing.py", line 163, in main
    raise FileNotFoundError(
FileNotFoundError: Input file data/processed/merged_root_soil.csv not found. Run data_ingestion.py (T015) first.

- python code/visualization.py -> rc=1

ERROR:root:Processed data not found at data/raw/processed/cleaned_data.csv. Run T015 first.


## Declared deliverables still missing

- data/raw/merged_dataset.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/merged_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/merged_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
