# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest tests/test_integration_fetch.py -v (rc=1); 3 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/graph_metrics.csv; data/processed/performance_metrics.csv

## Failing / missing run-book commands

- python -m pytest tests/test_integration_fetch.py -v -> rc=1
m credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.
ERROR tests/test_integration_fetch.py::test_fetch_backend_properties_with_retry - Failed: Failed to initialize QiskitRuntimeService: IBM Quantum credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.
ERROR tests/test_integration_fetch.py::test_validate_data_freshness - Failed: Failed to initialize QiskitRuntimeService: IBM Quantum credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.
ERROR tests/test_integration_fetch.py::test_extract_topology_and_metrics - Failed: Failed to initialize QiskitRuntimeService: IBM Quantum credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.
ERROR tests/test_integration_fetch.py::test_full_fetch_pipeline_with_save - Failed: Failed to initialize QiskitRuntimeService: IBM Quantum credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.
ERROR tests/test_integration_fetch.py::test_rate_limit_handling - Failed: Failed to initialize QiskitRuntimeService: IBM Quantum credentials not found. Please set IBMQ_TOKEN or run 'ibm quantum save'.
============================== 6 errors in 1.40s ===============================



## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/graph_metrics.csv
- data/processed/performance_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_mdes_report_section.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_graph_metrics_csv.py` — NOT invoked by the run-book
    - `code/graph_builder.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_graph_builder.py` — NOT invoked by the run-book
    - `code/tests/test_stats_engine.py` — NOT invoked by the run-book
    - `code/validate_graph_metrics_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fetcher.py` — NOT invoked by the run-book
    - `code/generate_calibration_csv.py` — NOT invoked by the run-book
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_processed_csv.py` — NOT invoked by the run-book
    - `code/tests/test_stats_engine.py` — NOT invoked by the run-book
    - `code/validate_performance_metrics_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
