# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipeline.run_all (rc=1); python -m pytest src/tests/ (rc=1); 9 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/features.parquet; data/raw/zenodo_corrosion.csv

## Failing / missing run-book commands

- python -m src.pipeline.run_all -> rc=1
met/src/pipeline/run_all.py", line 58, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/run_all.py", line 31, in main
    rc = ingest_main([])
         ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 429, in main
    raw_path = ingest(dataset_id=args.dataset_id, max_candidates=args.max_candidates)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 316, in ingest
    frame, mapping = fetch_dataset(
                     ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/src/pipeline/ingest.py", line 135, in fetch_dataset
    raise RuntimeError(
RuntimeError: Fallback download failed for https://github.com/selva86/datasets/raw/master/Corrosion.csv: 404 Client Error: Not Found for url: https://github.com/selva86/datasets/raw/master/Corrosion.csv

- python -m pytest src/tests/ -> rc=1
--------------------
        try:
            response = requests.get(FALLBACK_URL, timeout=30)
            response.raise_for_status()
        except Exception as exc:
>           raise RuntimeError(
                f"Fallback download failed for {FALLBACK_URL}: {exc}"
            ) from exc
E           RuntimeError: Fallback download failed for https://github.com/selva86/datasets/raw/master/Corrosion.csv: 404 Client Error: Not Found for url: https://github.com/selva86/datasets/raw/master/Corrosion.csv

src/pipeline/ingest.py:135: RuntimeError
=========================== short test summary info ============================
FAILED src/tests/test_ingest.py::test_ingest_creates_raw_and_provenance - Run...
FAILED src/tests/test_quickstart.py::test_quickstart_run_all - AssertionError...
FAILED src/tests/test_train.py::test_first_run_metrics_created - FileNotFound...
FAILED src/tests/test_vif.py::test_vif_diagnostics_created - RuntimeError: Fa...
ERROR src/tests/test_features.py::test_features_parquet_created - AssertionEr...
ERROR src/tests/test_features.py::test_feature_names_json - AssertionError: f...
==================== 4 failed, 2 passed, 2 errors in 5.73s =====================



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
    - `src/pipeline/features.py` — NOT invoked by the run-book
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
    - `src/pipeline/train.py` — NOT invoked by the run-book
    - `src/pipeline/vif.py` — NOT invoked by the run-book
    - `src/tests/test_ingest.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/features.py` — NOT invoked by the run-book
    - `src/pipeline/run_all.py` — IS a run-book command
    - `src/run_all.py` — NOT invoked by the run-book
    - `src/tests/test_features.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/zenodo_corrosion.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/bh_corrected_interaction_importance.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/feature_stability.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/interaction_gain_permutation_test.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/runtime_log.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/shap_interaction_rankings.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/vif_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/vif.py` — NOT invoked by the run-book
    - `src/tests/test_quickstart.py` — NOT invoked by the run-book
    - `src/tests/test_vif.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/vif_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
