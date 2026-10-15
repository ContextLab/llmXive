# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/analysis_dataset.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/analysis_dataset.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/ingestion.py --download-only (rc=1); python code/main.py (rc=1); python -m pytest tests/ -v (rc=2)

## Failing / missing run-book commands

- python code/ingestion.py --download-only -> rc=1
most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/ingestion.py", line 337, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/ingestion.py", line 308, in main
    df = pd.read_parquet(RAW_DATA_PATH)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 651, in read_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 67, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/main.py", line 49, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/main.py", line 40, in main
    config = Config.load(config_path)
             ^^^^^^^^^^^
AttributeError: type object 'Config' has no attribute 'load'

- python -m pytest tests/ -v -> rc=2
../../.llmxive-venvs/PROJ-334-predicting-avian-song-variation-with-cli/lib/python3.11/site-packages/geopandas/_compat.py:10
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-334-predicting-avian-song-variation-with-cli/lib/python3.11/site-packages/geopandas/_compat.py:10: DeprecationWarning: The 'shapely.geos' module is deprecated, and will be removed in a future version. All attributes of 'shapely.geos' are available directly from the top-level 'shapely' namespace (since shapely 2.0.0).
    import shapely.geos

code/setup_dependencies.py:5
  /home/runner/work/llmXive/llmXive/projects/PROJ-334-predicting-avian-song-variation-with-cli/code/setup_dependencies.py:5: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html
    import pkg_resources

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_ingestion_save.py
ERROR tests/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 2 errors in 0.72s =========================


