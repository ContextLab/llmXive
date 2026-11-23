# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash scripts/run_pipeline.sh; 8 command(s) failed: python code/01_data_ingestion.py (rc=1); python code/02_preprocessing.py (rc=1); python code/03_correlation_analysis.py (rc=1); 4 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/merged_monthly.csv; data/processed/noaa_preprocessed_control.csv

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=1
2026-10-11 09:28:42,171 - INFO - === Data Ingestion Pipeline Start ===
2026-10-11 09:28:42,171 - INFO - Starting GRACE-FO data ingestion...
2026-10-11 09:28:42,171 - INFO - Fetching GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc from https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
2026-10-11 09:28:42,404 - ERROR - Failed to fetch GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc: 404 Client Error: Not Found for url: https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
2026-10-11 09:28:42,404 - CRITICAL - GRACE-FO ingestion failed: Real data fetch failed for GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc: 404 Client Error: Not Found for url: https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc


- python code/02_preprocessing.py -> rc=1

2026-10-11 09:28:42,742 - INFO - Starting preprocessing and merge pipeline
2026-10-11 09:28:42,743 - ERROR - Failed to load raw data: No GRACE-FO CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/grace-fo

- python code/03_correlation_analysis.py -> rc=1

2026-10-11 09:28:43,316 - INFO - Starting correlation analysis...
2026-10-11 09:28:43,317 - CRITICAL - Merged data file not found: data/processed/merged_monthly.csv. Run T017c first.

- python code/04_visualization.py -> rc=1

2026-10-11 09:28:44,188 - INFO - === Visualization Pipeline Start ===
2026-10-11 09:28:44,188 - ERROR - Merged data file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv. Run preprocessing pipeline first.

- python code/05_sensitivity_report.py -> rc=1

2026-10-11 09:28:44,542 - INFO - Starting Sensitivity Analysis...
2026-10-11 09:28:44,701 - ERROR - Merged data file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv
2026-10-11 09:28:44,701 - ERROR - Data loading failed: Required input file missing: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv

- bash scripts/run_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file
- python -m pytest tests/contract/ -> rc=1
ma
    raise FileNotFoundError(f"Test data not found: {data_path}")
E   FileNotFoundError: Test data not found: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv
________________________ test_sensitivity_report_exists ________________________
tests/contract/test_sensitivity_report.py:7: in test_sensitivity_report_exists
    assert os.path.exists('output/sensitivity_report.md'), "Sensitivity report not found"
E   AssertionError: Sensitivity report not found
E   assert False
E    +  where False = <function exists at 0x7f30febe3920>('output/sensitivity_report.md')
E    +    where <function exists at 0x7f30febe3920> = <module 'posixpath' (frozen)>.exists
E    +      where <module 'posixpath' (frozen)> = os.path
=========================== short test summary info ============================
FAILED tests/contract/test_correlation_schema.py::test_correlation_schema - F...
FAILED tests/contract/test_dataset_schema.py::test_merged_schema - FileNotFou...
FAILED tests/contract/test_sensitivity_report.py::test_sensitivity_report_exists
==================== 3 failed, 2 passed, 2 skipped in 0.26s ====================


- python -m pytest tests/integration/ -> rc=2

rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos
configfile: pyproject.toml
collecting ... collected 2 items / 1 error

==================================== ERRORS ====================================
___________ ERROR collecting tests/integration/test_merge_output.py ____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_merge_output.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_merge_output.py:21: in <module>
    from code_03_merge_output import (
E   ModuleNotFoundError: No module named 'code_03_merge_output'
=========================== short test summary info ============================
ERROR tests/integration/test_merge_output.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.30s ===============================


- python code/verify_completeness.py --threshold 0.90 -> rc=1
ion_results.csv'
2026-10-11 09:28:45,913 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/output/timeseries_overlay.png
2026-10-11 09:28:45,913 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/output/scatter_regression.png
2026-10-11 09:28:45,913 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/output/spatial_anomaly_map.png
2026-10-11 09:28:45,913 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/docs/sensitivity_report.md
2026-10-11 09:28:45,913 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/docs/temporal_bias_analysis.md
2026-10-11 09:28:45,913 - INFO - Completeness: 0.00% (0/7)
2026-10-11 09:28:45,913 - ERROR - Failed checks for: merged_monthly_csv, correlation_results_csv, timeseries_plot, scatter_plot, spatial_plot, sensitivity_report, temporal_bias_doc
2026-10-11 09:28:45,913 - ERROR - FAILURE: Completeness 0.00% is below threshold 90.00%.


## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/merged_monthly.csv
- data/processed/noaa_preprocessed_control.csv
- data/processed/noaa_preprocessed_target.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_correlation.py` — NOT invoked by the run-book
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/04_bootstrap_correction.py` — NOT invoked by the run-book
    - `code/04_runtime_profiler.py` — NOT invoked by the run-book
    - `code/05_bootstrap_correction.py` — NOT invoked by the run-book
    - `code/05_control_validation.py` — NOT invoked by the run-book
    - `code/06_control_validation.py` — NOT invoked by the run-book
    - `code/09_sensitivity_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_monthly.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing.py` — IS a run-book command
    - `code/02_preprocessing_merge.py` — NOT invoked by the run-book
    - `code/03_correlation.py` — NOT invoked by the run-book
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/03_merge_output.py` — NOT invoked by the run-book
    - `code/04_bootstrap_correction.py` — NOT invoked by the run-book
    - `code/04_runtime_profiler.py` — NOT invoked by the run-book
    - `code/04_visualization.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merged_monthly.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noaa_preprocessed_control.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing_noaa.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noaa_preprocessed_control.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noaa_preprocessed_target.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocessing_noaa.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noaa_preprocessed_target.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
