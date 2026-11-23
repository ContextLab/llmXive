# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --input data/processed/cleaned.parquet --output data/output/`
  - script usage: `main.py [-h] [--spec-file SPEC_FILE] [--output-dir OUTPUT_DIR]`
  - argparse error: `main.py: error: unrecognized arguments: --input data/processed/cleaned.parquet`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/ingest/download.py --dataset-url <verified-url> (rc=1); python code/main.py --input data/processed/cleaned.parquet --output data/output/ (rc=2); python code/viz/plots.py --input data/output/analysis.json --output data/output/plots/ (rc=1); 1 declared deliverable(s) absent: data/output/citation_validation.json

## Failing / missing run-book commands

- python code/ingest/download.py --dataset-url <verified-url> -> rc=1

Download failed!

2026-10-17 21:21:02 - llmXive.ingest.ingest - INFO - Operation 'Dataset download script' started - 
2026-10-17 21:21:02 - llmXive.ingest.ingest - INFO - Operation 'Downloading dataset from --dataset-url' started - 
2026-10-17 21:21:02 - llmXive.ingest.ingest - INFO - Saving to <verified-url>
2026-10-17 21:21:02 - llmXive.ingest.ingest - INFO - Operation 'Download failed' completed

- python code/main.py --input data/processed/cleaned.parquet --output data/output/ -> rc=2
============================================================
LLMXIVE AUTOMATED SCIENCE PIPELINE
Project: PROJ-462-evaluating-the-impact-of-code-generation
============================================================
[2026-10-17 21:21:02] Pipeline starting...

usage: main.py [-h] [--spec-file SPEC_FILE] [--output-dir OUTPUT_DIR]
               [--phase PHASE]
main.py: error: unrecognized arguments: --input data/processed/cleaned.parquet

- python code/viz/plots.py --input data/output/analysis.json --output data/output/plots/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/viz/plots.py", line 340, in main
    outputs = run_viz_pipeline(
              ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/viz/plots.py", line 292, in run_viz_pipeline
    log_operation_start("run_viz_pipeline")
TypeError: log_operation_start() missing 1 required positional argument: 'operation'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/viz/plots.py", line 362, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/viz/plots.py", line 357, in main
    log_error(f"Pipeline failed: {str(e)}")
TypeError: log_error() missing 1 required positional argument: 'message'

- python code/analysis/sensitivity.py --input data/processed/cleaned.parquet --thresholds 1 2 3 --output data/output/sensitivity.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/analysis/sensitivity.py", line 17, in <module>
    from analysis.anova import perform_two_way_anova, calculate_interaction_effect, ExtractedStats, AnovaResult
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/analysis/anova.py", line 12, in <module>
    logger = get_anova_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_anova_logger() takes 0 positional arguments but 1 was given

- python -m pytest tests/contract/ -> rc=1
act/test_visualization_schema.py::TestVisualizationSchema::test_missing_interaction_lines
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_missing_file_path
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_invalid_plot_type
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_empty_file_path
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_invalid_file_extension
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_all_valid_plot_types
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_interaction_lines_as_boolean
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_interaction_lines_as_list
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_schema_completeness
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_schema_type_definitions
ERROR tests/contract/test_visualization_schema.py::TestVisualizationSchema::test_schema_has_description
=================== 8 failed, 23 passed, 26 errors in 0.46s ====================


- python -m pytest tests/integration/ -> rc=2
========================= ERRORS ====================================
_ ERROR collecting projects/PROJ-462-evaluating-the-impact-of-code-generation/tests/integration/test_export_pipeline.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/tests/integration/test_export_pipeline.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_export_pipeline.py:19: in <module>
    from export.results import (
E   ImportError: cannot import name '_prepare_dataframe_for_csv' from 'export.results' (/home/runner/work/llmXive/llmXive/projects/PROJ-462-evaluating-the-impact-of-code-generation/code/export/results.py)
=========================== short test summary info ============================
ERROR tests/integration/test_export_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.46s ===============================


- python -m pytest tests/unit/ -> rc=2
est_experience_classification.py:16: in <module>
    from analysis.experience import (
E   ModuleNotFoundError: No module named 'analysis.experience'
_ ERROR collecting projects/PROJ-462-evaluating-the-impact-of-code-generation/tests/unit/test_sensitivity.py _
tests/unit/test_sensitivity.py:15: in <module>
    from analysis.sensitivity import (
code/analysis/sensitivity.py:17: in <module>
    from analysis.anova import perform_two_way_anova, calculate_interaction_effect, ExtractedStats, AnovaResult
code/analysis/anova.py:12: in <module>
    logger = get_anova_logger(__name__)
E   TypeError: get_anova_logger() takes 0 positional arguments but 1 was given
=========================== short test summary info ============================
ERROR tests/unit/test_anova.py - TypeError: get_anova_logger() takes 0 positi...
ERROR tests/unit/test_data_validation.py - TypeError: get_anova_logger() take...
ERROR tests/unit/test_experience_classification.py
ERROR tests/unit/test_sensitivity.py - TypeError: get_anova_logger() takes 0 ...
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.95s ===============================



## Declared deliverables still missing

- data/output/citation_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/output/citation_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/validate/citations.py` — NOT invoked by the run-book
    - `code/validate/generate_citation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/output/citation_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
