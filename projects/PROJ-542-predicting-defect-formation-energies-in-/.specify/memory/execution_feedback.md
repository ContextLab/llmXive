# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1); 1 declared deliverable(s) absent: figures/pred_vs_actual.png

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-22 18:35:07,736 WARNING src.data.featurize: Failed to parse composition 'ABX3' – Oxygen not found in composition 'ABX3'
2026-10-22 18:35:07,736 ERROR src.data.featurize: Featurization failed: All rows were dropped – no features to write.
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/featurize.py", line 17, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/featurize.py", line 14, in main
    _impl_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/data/featurize.py", line 293, in main
    compute_features(Path(args.input_csv), Path(args.output_csv))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/data/featurize.py", line 228, in compute_features
    raise RuntimeError("All rows were dropped – no features to write.")
RuntimeError: All rows were dropped – no features to write.

- python -m src.validate data/processed/features.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/validate.py", line 23, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/validate.py", line 20, in main
    _impl_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/data/validate.py", line 57, in main
    raise ValueError("Insufficient rows (<50) for 5-fold CV")
ValueError: Insufficient rows (<50) for 5-fold CV

- python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.split

- python -m src.train data/processed/train.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
:34
  /home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/tests/test_train.py:34: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_feature_importance.py::test_feature_importance_populates_json_and_figure
FAILED code/tests/test_run_fallback.py::test_run_fallback_executes - subproce...
FAILED code/tests/test_run_fallback.py::test_run_fallback_integration - subpr...
FAILED src/tests/test_descriptor_gaps.py::test_check_descriptor_gaps_with_missing
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - AssertionErro...
FAILED src/tests/test_train.py::test_training_produces_outputs - AssertionErr...
FAILED tests/test_split.py::test_split_dataset_basic - assert 2 <= 1
FAILED tests/test_split.py::test_cli_execution - AssertionError: assert False
8 failed, 9 passed, 16 warnings in 6.82s



## Declared deliverables still missing

- figures/pred_vs_actual.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `figures/pred_vs_actual.png` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_run_fallback.py` — NOT invoked by the run-book
    - `src/models/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/pred_vs_actual.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
