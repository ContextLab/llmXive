# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python code/01_data_ingestion.py (rc=1); python code/02_preprocessing.py (rc=1); python code/02_preprocessing.py --power-analysis (rc=1); 4 declared deliverable(s) absent: data/artifacts/basin_variance_viz.png; data/logs/missing_value_report.json; data/processed/split_indices.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=1
2026-10-19 15:32:59 - __main__ - INFO - Starting data ingestion and quality filtering pipeline (T015)
2026-10-19 15:32:59 - __main__ - ERROR - Pipeline execution failed: No MODIS data file found in data/raw/.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/01_data_ingestion.py", line 283, in main
    modis_df = load_modis_quality_flags()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/01_data_ingestion.py", line 47, in load_modis_quality_flags
    raise FileNotFoundError("No MODIS data file found in data/raw/.")
FileNotFoundError: No MODIS data file found in data/raw/.


- python code/02_preprocessing.py -> rc=1
2026-10-19 15:33:00 - __main__ - INFO - Starting preprocessing pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/02_preprocessing.py", line 331, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/02_preprocessing.py", line 258, in main
    memory_limit = config.get('memory_limit_gb', 7.0)
                   ^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'get'

- python code/02_preprocessing.py --power-analysis -> rc=1
2026-10-19 15:33:00 - __main__ - INFO - Starting preprocessing pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/02_preprocessing.py", line 331, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/02_preprocessing.py", line 258, in main
    memory_limit = config.get('memory_limit_gb', 7.0)
                   ^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'get'

- python code/03_model_training.py -> rc=1

Data not found: Aligned data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/data/processed/aligned_dataset.nc

- python code/04_evaluation.py -> rc=1
2026-10-19 15:33:05,104 - __main__ - INFO - Starting Basin Variance Report Generation (T020a)...
2026-10-19 15:33:05,104 - __main__ - ERROR - T020a failed: Model comparison artifact not found at data/artifacts/model_comparison.csv. Ensure T020 has been executed successfully.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/04_evaluation.py", line 221, in main
    calculate_basin_r2_difference()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/04_evaluation.py", line 43, in calculate_basin_r2_difference
    data = load_model_artifacts()
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/04_evaluation.py", line 32, in load_model_artifacts
    raise FileNotFoundError(f"Model comparison artifact not found at {model_path}. "
FileNotFoundError: Model comparison artifact not found at data/artifacts/model_comparison.csv. Ensure T020 has been executed successfully.


- python code/05_versioning_state.py -> rc=1

ERROR: Reanalysis file not found at data/raw/copernicus_global_reanalysis.nc

- python -m pytest tests/contract/ -> rc=1
: '/home/runner/work/llmXive/llmXive/projects/PROJ-021-understanding-oceanic-phytoplankton-comm/code/specs/001-understanding-oceanic-phytoplankton-comm/contracts/aligned_dataset.schema.yaml'

tests/contract/test_schemas.py:13: FileNotFoundError
=========================== short test summary info ============================
FAILED tests/contract/test_feature_importance_schema.py::TestFeatureImportanceSchema::test_schema_file_exists
FAILED tests/contract/test_feature_importance_schema.py::TestFeatureImportanceSchema::test_schema_is_valid_yaml
FAILED tests/contract/test_feature_importance_schema.py::TestFeatureImportanceSchema::test_schema_has_required_properties
FAILED tests/contract/test_feature_importance_schema.py::TestFeatureImportanceSchema::test_schema_validates_sum_to_unity
FAILED tests/contract/test_feature_importance_schema.py::TestFeatureImportanceSchema::test_schema_rejects_non_unity_sum
FAILED tests/contract/test_feature_importance_schema.py::TestFeatureImportanceSchema::test_schema_validates_importance_values
FAILED tests/contract/test_schemas.py::test_aligned_dataset_schema - FileNotF...
========================= 7 failed, 2 skipped in 0.07s =========================


- python -m pytest tests/integration/test_pipeline.py -v --tb=short -> rc=1
ifacts/basin_variance_report.md')>()
E    +    where <bound method Path.exists of PosixPath('data/artifacts/basin_variance_report.md')> = PosixPath('data/artifacts/basin_variance_report.md').exists
___________________________ test_kruskal_wallis_test ___________________________
tests/integration/test_pipeline.py:97: in test_kruskal_wallis_test
    assert result_path.exists(), "Kruskal-Wallis test results are missing."
E   AssertionError: Kruskal-Wallis test results are missing.
E   assert False
E    +  where False = <bound method Path.exists of PosixPath('data/artifacts/basin_variance_significance.json')>()
E    +    where <bound method Path.exists of PosixPath('data/artifacts/basin_variance_significance.json')> = PosixPath('data/artifacts/basin_variance_significance.json').exists
=========================== short test summary info ============================
FAILED tests/integration/test_pipeline.py::test_feature_importance_maps_generation
FAILED tests/integration/test_pipeline.py::test_basin_variance_report - Asser...
FAILED tests/integration/test_pipeline.py::test_kruskal_wallis_test - Asserti...
========================= 3 failed, 1 passed in 0.24s ==========================



## Declared deliverables still missing

- data/artifacts/basin_variance_viz.png
- data/logs/missing_value_report.json
- data/processed/split_indices.json
- data/raw/seabass.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/basin_variance_viz.png` is declared but was NOT written. Scripts referencing it:
    - `code/04_evaluation.py` — IS a run-book command
  Make ONE of these WRITE `data/artifacts/basin_variance_viz.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/missing_value_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/logs/missing_value_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/seabass.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/01_fetch_seabass.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/seabass.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
