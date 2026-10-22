# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipeline.run_all (rc=1); python -m pytest src/tests/ (rc=1); 9 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/features.parquet; data/raw/zenodo_corrosion.csv

## Failing / missing run-book commands

- python -m src.pipeline.run_all -> rc=1
xit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/run_all.py", line 40, in main
    rc = step_fn([])
         ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 535, in main
    raw_path = ingest(
               ^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 411, in ingest
    frame, mapping = fetch_dataset(
                     ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 296, in fetch_dataset
    df, mapping = _download_fallback()
                  ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 190, in _download_fallback
    raise RuntimeError(
RuntimeError: All fallback URLs failed. Last error: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/selva86/datasets/master/corrosion.csv

- python -m pytest src/tests/ -> rc=1
icting-corrosion-rates-of-common-met/src/pipeline/ingest.py:199: FutureWarning: Starting from Version 0.15 `download_data`, `download_qualities`, and `download_features_meta_data` will all be ``False`` instead of ``True`` by default to enable lazy loading. To disable this message until version 0.15 explicitly set `download_data`, `download_qualities`, and `download_features_meta_data` to a bool while calling `get_dataset`.
    oml_dataset = openml.datasets.get_dataset(did)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED src/tests/test_ingest.py::test_ingest_creates_raw_and_provenance - Run...
FAILED src/tests/test_quickstart.py::test_quickstart_run_all - AssertionError...
FAILED src/tests/test_train.py::test_first_run_metrics_created - AssertionErr...
FAILED src/tests/test_vif.py::test_vif_diagnostics_created - RuntimeError: Al...
ERROR src/tests/test_features.py::test_features_parquet_created - AssertionEr...
ERROR src/tests/test_features.py::test_feature_names_json - AssertionError: f...
============== 4 failed, 2 passed, 2 warnings, 2 errors in 14.05s ==============



## Declared deliverables still missing

- data/processed/cleaned_dataset.csv
- data/processed/features.parquet
- data/raw/zenodo_corrosion.csv
- data/results/bh_corrected_interaction_importance.json
- data/results/feature_stability.json
- data/results/interaction_gain_permutation_test.json
- data/results/runtime_log.json
- data/results/shap_interaction_rankings.json
- data/results/vif_diagnostics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/evaluate.py` — NOT invoked by the run-book
    - `src/pipeline/features.py` — NOT invoked by the run-book
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
    - `src/pipeline/split.py` — NOT invoked by the run-book
    - `src/pipeline/train.py` — NOT invoked by the run-book
    - `src/pipeline/vif.py` — NOT invoked by the run-book
    - `src/tests/test_ingest.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/evaluate.py` — NOT invoked by the run-book
    - `src/pipeline/features.py` — NOT invoked by the run-book
    - `src/pipeline/run_all.py` — IS a run-book command
    - `src/run_all.py` — NOT invoked by the run-book
    - `src/tests/test_features.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/zenodo_corrosion.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/bh_corrected_interaction_importance.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/feature_stability.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/interaction_gain_permutation_test.json` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/interaction_gain_permutation_test.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_log.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/shap_interaction_rankings.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/vif_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/vif.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
    - `src/tests/test_vif.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/vif_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
