# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/01_data_ingestion.py (rc=1); python code/02_preprocessing.py (rc=1); python code/03_correlation_analysis.py (rc=1); 2 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/merged_monthly.csv

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=1
    2026-09-02 15:25:06,039 - INFO - === Data Ingestion Pipeline Start ===
2026-09-02 15:25:06,039 - INFO - Starting GRACE-FO data ingestion...
2026-09-02 15:25:06,039 - INFO - Fetching GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc from https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
2026-09-02 15:25:06,397 - ERROR - Failed to fetch GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc: 404 Client Error: Not Found for url: https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
2026-09-02 15:25:06,397 - CRITICAL - GRACE-FO ingestion failed: Real data fetch failed for GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc: 404 Client Error: Not Found for url: https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
- python code/02_preprocessing.py -> rc=1
    2026-09-02 15:25:07,152 - INFO - Starting preprocessing and merge pipeline
2026-09-02 15:25:07,153 - ERROR - Failed to load raw data: No GRACE-FO CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/grace-fo
- python code/03_correlation_analysis.py -> rc=1
    2026-09-02 15:25:08,594 - INFO - Starting correlation analysis...
2026-09-02 15:25:08,594 - CRITICAL - Analysis failed: Merged data file not found: data/processed/merged_monthly.csv. Run T017c first.
- python code/04_visualization.py -> rc=1
    2026-09-02 15:25:10,380 - INFO - === Visualization Pipeline Start ===
2026-09-02 15:25:10,380 - ERROR - Merged data file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv. Run preprocessing pipeline first.
- python code/05_sensitivity_report.py -> rc=1
    2026-09-02 15:25:10,903 - INFO - Starting Sensitivity Analysis...
2026-09-02 15:25:11,490 - ERROR - Merged data file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv
2026-09-02 15:25:11,490 - ERROR - Data loading failed: Required input file missing: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv
- python code/verify_completeness.py --threshold 0.90 -> rc=1
    ion_results.csv'
2026-09-02 15:25:11,912 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/output/timeseries_overlay.png
2026-09-02 15:25:11,912 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/output/scatter_regression.png
2026-09-02 15:25:11,912 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/output/spatial_anomaly_map.png
2026-09-02 15:25:11,912 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/docs/sensitivity_report.md
2026-09-02 15:25:11,912 - ERROR - Missing file: /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/docs/temporal_bias_analysis.md
2026-09-02 15:25:11,912 - INFO - Completeness: 0.00% (0/7)
2026-09-02 15:25:11,912 - ERROR - Failed checks for: merged_monthly_csv, correlation_results_csv, timeseries_plot, scatter_plot, spatial_plot, sensitivity_report, temporal_bias_doc
2026-09-02 15:25:11,912 - ERROR - FAILURE: Completeness 0.00% is below threshold 90.00%.

## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/merged_monthly.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/05_control_validation.py` — NOT invoked by the run-book
    - `code/06_control_validation.py` — NOT invoked by the run-book
    - `code/09_sensitivity_report.py` — NOT invoked by the run-book
    - `code/04_runtime_profiler.py` — NOT invoked by the run-book
    - `code/05_bootstrap_correction.py` — NOT invoked by the run-book
    - `code/03_correlation.py` — NOT invoked by the run-book
    - `code/04_bootstrap_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_monthly.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_merge_output.py` — NOT invoked by the run-book
    - `code/07_visualization_timeseries.py` — NOT invoked by the run-book
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/05_control_validation.py` — NOT invoked by the run-book
    - `code/06_control_validation.py` — NOT invoked by the run-book
    - `code/04_visualization.py` — IS a run-book command
    - `code/02_preprocessing.py` — IS a run-book command
    - `code/02_preprocessing_merge.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_monthly.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/merged_monthly.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_merge_output.py`, `code/03_correlation_analysis.py`, `code/05_control_validation.py`, `code/06_control_validation.py`, `code/02_preprocessing.py`, `code/02_preprocessing_merge.py`, `code/04_runtime_profiler.py`, `code/05_bootstrap_correction.py`, `code/05_sensitivity_report.py`, `code/10_temporal_bias_analysis.py`, `code/03_correlation.py`, `code/04_bootstrap_correction.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/merged_monthly.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_merge_output.py`, `code/07_visualization_timeseries.py`, `code/03_correlation_analysis.py`, `code/05_control_validation.py`, `code/06_control_validation.py`, `code/04_visualization.py`, `code/02_preprocessing.py`, `code/02_preprocessing_merge.py`, `code/04_runtime_profiler.py`, `code/05_bootstrap_correction.py`, `code/05_sensitivity_report.py`, `code/10_temporal_bias_analysis.py`, `code/03_correlation.py`, `code/04_bootstrap_correction.py`, `code/verify_completeness.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_merge_output.py`, `code/03_correlation_analysis.py`, `code/05_control_validation.py`, `code/06_control_validation.py`, `code/02_preprocessing.py`, `code/02_preprocessing_merge.py`, `code/04_runtime_profiler.py`, `code/05_bootstrap_correction.py`, `code/05_sensitivity_report.py`, `code/10_temporal_bias_analysis.py`, `code/03_correlation.py`, `code/04_bootstrap_correction.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_merge_output.py`, `code/07_visualization_timeseries.py`, `code/03_correlation_analysis.py`, `code/05_control_validation.py`, `code/06_control_validation.py`, `code/04_visualization.py`, `code/02_preprocessing.py`, `code/02_preprocessing_merge.py`, `code/04_runtime_profiler.py`, `code/05_bootstrap_correction.py`, `code/05_sensitivity_report.py`, `code/10_temporal_bias_analysis.py`, `code/03_correlation.py`, `code/04_bootstrap_correction.py`, `code/verify_completeness.py`.
