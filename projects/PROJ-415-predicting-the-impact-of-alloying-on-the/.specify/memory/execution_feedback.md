# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/data/streaming_loader.py; python code/processing/feature_engineering.py; python code/models/train_rf.py; 1 command(s) failed: python -m pytest tests/ -v (rc=2); 1 declared deliverable(s) absent: data/curated/data_provenance.json

## Failing / missing run-book commands

- python code/data/streaming_loader.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-415-predicting-the-impact-of-alloying-on-the/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/code/data/streaming_loader.py': [Errno 2] No such file or directory

- python code/processing/feature_engineering.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-415-predicting-the-impact-of-alloying-on-the/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/code/processing/feature_engineering.py': [Errno 2] No such file or directory

- python code/models/train_rf.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-415-predicting-the-impact-of-alloying-on-the/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/code/models/train_rf.py': [Errno 2] No such file or directory

- python code/models/train_gb.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-415-predicting-the-impact-of-alloying-on-the/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/code/models/train_gb.py': [Errno 2] No such file or directory

- python code/models/train_linear.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-415-predicting-the-impact-of-alloying-on-the/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/code/models/train_linear.py': [Errno 2] No such file or directory

- python code/validation/sensitivity_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-415-predicting-the-impact-of-alloying-on-the/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/code/validation/sensitivity_analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
gration/test_data_structure.py
ERROR tests/integration/test_model_training.py
ERROR tests/integration/test_pipeline.py
ERROR tests/integration/test_sensitivity_stability.py
ERROR tests/test_acquisition.py
ERROR tests/unit/test_acquisition.py
ERROR tests/unit/test_baseline.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_constants.py
ERROR tests/unit/test_curation.py
ERROR tests/unit/test_curation_edge_cases.py
ERROR tests/unit/test_edge_cases.py
ERROR tests/unit/test_gridsearch_fallback.py
ERROR tests/unit/test_inference.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_linting_setup.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_models.py
ERROR tests/unit/test_project_structure.py
ERROR tests/unit/test_report_generator.py
ERROR tests/unit/test_save_artifacts.py
ERROR tests/unit/test_sensitivity.py
ERROR tests/unit/test_sensitivity_csv.py
ERROR tests/unit/test_setup_data_dirs.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_training_robustness.py
ERROR tests/validation/test_baseline.py
!!!!!!!!!!!!!!!!!!! Interrupted: 28 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 28 errors in 1.92s ==============================



## Declared deliverables still missing

- data/curated/data_provenance.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated/data_provenance.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/curation.py` — NOT invoked by the run-book
    - `code/models/training.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/curated/data_provenance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
