# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipeline.run_all (rc=1); python -m pytest src/tests/ (rc=1); 12 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/features.parquet; data/results/bh_interaction_importance.json

## Failing / missing run-book commands

- python -m src.pipeline.run_all -> rc=1
jects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 165, in _fetch_with_metadata
    df, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 485, in _fetch
    return _fetch_with_metadata(dataset_id, max_candidates)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 165, in _fetch_with_metadata
    df, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 485, in _fetch
    return _fetch_with_metadata(dataset_id, max_candidates)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
RecursionError: maximum recursion depth exceeded

- python -m pytest src/tests/ -> rc=1
ngest(dataset_id=args.dataset_id, max_candidates=args.max_candidates)
src/pipeline/ingest.py:365: in ingest
    frame, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)
src/pipeline/ingest.py:485: in _fetch
    return _fetch_with_metadata(dataset_id, max_candidates)
src/pipeline/ingest.py:165: in _fetch_with_metadata
    df, mapping = fetch_dataset(dataset_id=dataset_id, max_candidates=max_candidates)
src/pipeline/ingest.py:485: in _fetch
    return _fetch_with_metadata(dataset_id, max_candidates)
E   RecursionError: maximum recursion depth exceeded
!!! Recursion detected (same locals & position)
=========================== short test summary info ============================
FAILED src/tests/test_ingest.py::test_ingest_creates_raw_and_provenance - Rec...
FAILED src/tests/test_train.py::test_first_run_metrics_created - FileNotFound...
FAILED src/tests/test_vif.py::test_vif_diagnostics_created - RecursionError: ...
ERROR src/tests/test_features.py::test_features_parquet_created - AssertionEr...
ERROR src/tests/test_features.py::test_feature_names_json - AssertionError: f...
========================= 3 failed, 2 errors in 1.07s ==========================



## Declared deliverables still missing

- data/processed/cleaned_dataset.csv
- data/processed/features.parquet
- data/results/bh_interaction_importance.json
- data/results/first_run_metrics.json
- data/results/heldout_metrics.json
- data/results/interaction_test.json
- data/results/runtime_log.json
- data/results/sensitivity_maxdepth.json
- data/results/shap_interaction_matrix.npy
- data/results/shap_rankings.json
- data/results/target_perm_fullnull.json
- data/results/vif_diagnostics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/features.py` — NOT invoked by the run-book
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
    - `src/pipeline/train.py` — NOT invoked by the run-book
    - `src/pipeline/vif.py` — NOT invoked by the run-book
    - `src/tests/test_ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/features.py` — NOT invoked by the run-book
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
    - `src/pipeline/run_all.py` — IS a run-book command
    - `src/tests/test_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/bh_interaction_importance.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/first_run_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/evaluate.py` — NOT invoked by the run-book
    - `src/pipeline/train.py` — NOT invoked by the run-book
    - `src/tests/test_train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/first_run_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/heldout_metrics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/interaction_test.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/runtime_log.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/sensitivity_maxdepth.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/shap_interaction_matrix.npy` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/shap_rankings.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/target_perm_fullnull.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/vif_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/vif.py` — NOT invoked by the run-book
    - `src/tests/test_vif.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/vif_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
