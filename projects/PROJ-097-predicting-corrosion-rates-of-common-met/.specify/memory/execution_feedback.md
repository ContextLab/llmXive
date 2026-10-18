# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipeline.run_all (rc=1); python -m pytest src/tests/ (rc=1); 12 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/features.parquet; data/results/bh_interaction_importance.json

## Failing / missing run-book commands

- python -m src.pipeline.run_all -> rc=1
ine/ingest.py", line 309, in _fetch_with_metadata
    import openml
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-097-predicting-corrosion-rates-of-common-met/lib/python3.11/site-packages/openml/__init__.py", line 127, in <module>
    import openml.extensions.sklearn  # noqa: E402, F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-097-predicting-corrosion-rates-of-common-met/lib/python3.11/site-packages/openml/extensions/sklearn/__init__.py", line 8, in <module>
    from .extension import SklearnExtension
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-097-predicting-corrosion-rates-of-common-met/lib/python3.11/site-packages/openml/extensions/sklearn/extension.py", line 53, in <module>
    for type_cat, nptypes in np.sctypes.items()
                             ^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-097-predicting-corrosion-rates-of-common-met/lib/python3.11/site-packages/numpy/__init__.py", line 397, in __getattr__
    raise AttributeError(
AttributeError: `np.sctypes` was removed in the NumPy 2.0 release. Access dtypes explicitly instead.. Did you mean: 'dtypes'?

- python -m pytest src/tests/ -> rc=1
r(
                f"`np.{attr}` was removed in the NumPy 2.0 release. "
                f"{__expired_attributes__[attr]}"
            )
E           AttributeError: `np.sctypes` was removed in the NumPy 2.0 release. Access dtypes explicitly instead.

../../.llmxive-venvs/PROJ-097-predicting-corrosion-rates-of-common-met/lib/python3.11/site-packages/numpy/__init__.py:397: AttributeError
----------------------------- Captured stderr call -----------------------------
2026-10-18 17:14:23,458 INFO openml.config: Error opening file /home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/.runtime-home/.config/openml/config: not readable
------------------------------ Captured log call -------------------------------
INFO     openml.config:config.py:328 Error opening file /home/runner/work/llmXive/llmXive/projects/PROJ-097-predicting-corrosion-rates-of-common-met/.runtime-home/.config/openml/config: not readable
=========================== short test summary info ============================
FAILED src/tests/test_ingest.py::test_ingest_creates_raw_and_provenance - Att...
============================== 1 failed in 1.29s ===============================



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

- `data/processed/cleaned_dataset.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/features.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/bh_interaction_importance.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/first_run_metrics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/heldout_metrics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/interaction_test.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/runtime_log.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/sensitivity_maxdepth.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/shap_interaction_matrix.npy` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/shap_rankings.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/target_perm_fullnull.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/vif_diagnostics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
