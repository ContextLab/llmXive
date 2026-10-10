# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/reproducibility_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/reproducibility_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/ingestion.py (rc=1); python code/preprocessing.py (rc=1); python code/modeling.py (rc=1); 4 declared deliverable(s) absent: data/processed/ipw_weights.parquet; data/processed/merge_stats.json; data/processed/merged_sample.parquet

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/ingestion.py", line 47, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/ingestion.py", line 25, in main
    download_lsms_batch()
TypeError: download_lsms_batch() missing 2 required positional arguments: 'countries' and 'years'

- python code/preprocessing.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/preprocessing.py", line 36, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/preprocessing.py", line 28, in main
    run_sampling_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/utils/logging.py", line 68, in _wrapper
    return func(*a, **k)
           ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/data/clean.py", line 240, in run_sampling_pipeline
    raise FileNotFoundError("No LSMS data found in raw directory. Run download pipeline first.")
FileNotFoundError: No LSMS data found in raw directory. Run download pipeline first.

- python code/modeling.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/modeling.py", line 24, in <module>
    from data.features import main as features_main
ModuleNotFoundError: No module named 'data.features'

- python code/analysis/robustness.py --data data/processed/merged_sample.parquet --formula "hdds ~ csa_index + digital_access + finance_access + (digital_access * finance_access)" -> rc=1

INFO Loading data from data/processed/merged_sample.parquet
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/analysis/robustness.py", line 408, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/analysis/robustness.py", line 368, in main
    raise FileNotFoundError(f"Data file not found: {args.data}")
FileNotFoundError: Data file not found: data/processed/merged_sample.parquet

- python code/viz.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz.py", line 28, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz.py", line 21, in main
    viz_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz/plots.py", line 68, in main
    df = load_processed_data()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz/plots.py", line 17, in load_processed_data
    raise FileNotFoundError(f"Data not found: {path}")
FileNotFoundError: Data not found: data/processed/features.parquet


## Declared deliverables still missing

- data/processed/ipw_weights.parquet
- data/processed/merge_stats.json
- data/processed/merged_sample.parquet
- data/processed/provenance_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/ipw_weights.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/verify_reproducibility.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ipw_weights.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merge_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/verify_reproducibility.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merge_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/performance.py` — NOT invoked by the run-book
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/data/features.py` — NOT invoked by the run-book
    - `code/validation/quickstart_validator.py` — NOT invoked by the run-book
    - `code/verify_reproducibility.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merged_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/provenance_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/__init__.py` — NOT invoked by the run-book
    - `code/utils/logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/provenance_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
