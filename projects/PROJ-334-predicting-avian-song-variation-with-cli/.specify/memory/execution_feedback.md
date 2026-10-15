# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/analysis_dataset.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/analysis_dataset.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python code/ingestion.py --download-only (rc=1); python -m pytest tests/ -v (rc=2)

## Failing / missing run-book commands

- python code/ingestion.py --download-only -> rc=1
et
2026-10-15 16:46:47,984 INFO __main__: Download completed.
2026-10-15 16:46:48,141 INFO __main__: SHA‑256 checksum: 7ae2175aecd332fb045452f833c3f7d4044f7b946c91f5bd627d0e8094a40fb0
2026-10-15 16:46:48,141 INFO __main__: Recording checksum for analysis_dataset.parquet
2026-10-15 16:46:48,142 INFO __main__: Checksum for analysis_dataset.parquet already recorded.
2026-10-15 16:46:48,142 INFO __main__: Project state file updated.
2026-10-15 16:46:49,313 INFO __main__: Loaded analysis dataset with 5774 rows.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/ingestion.py", line 420, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/ingestion.py", line 398, in main
    validate_merge(df, logger)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/ingestion.py", line 224, in validate_merge
    mismatched_count = int(mismatched_mask.sum())
                           ^^^^^^^^^^^^^^^^^^^
AttributeError: 'bool' object has no attribute 'sum'

- python -m pytest tests/ -v -> rc=2
ry ===============================
../../.llmxive-venvs/PROJ-334-predicting-avian-song-variation-with-cli/lib/python3.11/site-packages/geopandas/_compat.py:10
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-334-predicting-avian-song-variation-with-cli/lib/python3.11/site-packages/geopandas/_compat.py:10: DeprecationWarning: The 'shapely.geos' module is deprecated, and will be removed in a future version. All attributes of 'shapely.geos' are available directly from the top-level 'shapely' namespace (since shapely 2.0.0).
    import shapely.geos

code/setup_dependencies.py:5
  /home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/setup_dependencies.py:5: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html
    import pkg_resources

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_utils.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 2 warnings, 1 error in 0.57s =========================


