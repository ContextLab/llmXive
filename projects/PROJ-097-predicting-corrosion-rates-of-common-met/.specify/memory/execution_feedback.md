# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/cleaned_dataset.csv: column(s) crystal_structure are EMPTY in every one of 344 rows — that measure was never recorded
- every produced artifact is gitignored (data/processed/cleaned_dataset.csv, data/raw/zenodo_corrosion.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/cleaned_dataset.csv: column(s) crystal_structure are EMPTY in every one of 344 rows — that measure was never recorded; every produced artifact is gitignored (data/processed/cleaned_dataset.csv, data/raw/zenodo_corrosion.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python -m src.run_all (rc=1); python -m pytest src/tests/ (rc=1)

## Failing / missing run-book commands

- python -m src.run_all -> rc=1
icting-corrosion-rates-of-common-met/src/pipeline/features.py", line 182, in main
    feature_df = build_features(cleaned_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/features.py", line 154, in build_features
    residualized[name] = _residualize(series, predictors)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/features.py", line 78, in _residualize
    beta, *_ = np.linalg.lstsq(X.values, series.values, rcond=None)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-097-predicting-corrosion-rates-of-common-met/lib/python3.11/site-packages/numpy/linalg/_linalg.py", line 2508, in lstsq
    x, resids, rank, s = gufunc(a, b, rcond, signature=signature)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
numpy._core._exceptions._UFuncInputCastingError: Cannot cast ufunc 'lstsq_n' input 0 from dtype('O') to dtype('float64') with casting rule 'same_kind'

- python -m pytest src/tests/ -> rc=1
gh chained assignment using an inplace method.
  The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.
  
  For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.
  
  
    df[col].fillna(mode, inplace=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED src/tests/test_ingest.py::test_ingest_creates_raw_and_provenance - Ass...
FAILED src/tests/test_quickstart.py::test_quickstart_run_all - AssertionError...
FAILED src/tests/test_train.py::test_first_run_metrics_created - AssertionErr...
FAILED src/tests/test_vif.py::test_vif_diagnostics_created - AssertionError: ...
ERROR src/tests/test_features.py::test_features_parquet_created - numpy._core...
ERROR src/tests/test_features.py::test_feature_names_json - numpy._core._exce...
============== 4 failed, 2 passed, 8 warnings, 2 errors in 9.39s ===============


