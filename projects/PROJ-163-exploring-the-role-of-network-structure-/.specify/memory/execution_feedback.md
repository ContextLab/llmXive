# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest tests/test_integration_fetch.py -v (rc=1); 3 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/graph_metrics.csv; data/processed/performance_metrics.csv

## Failing / missing run-book commands

- python -m pytest tests/test_integration_fetch.py -v -> rc=1
full_fetch_pipeline_with_save ______________________
tests/test_integration_fetch.py:197: in test_full_fetch_pipeline_with_save
    assert processed_count > 0, "At least one backend should have been processed and saved."
E   AssertionError: At least one backend should have been processed and saved.
E   assert 0 > 0
----------------------------- Captured stderr call -----------------------------
2026-10-16 09:18:58,521 INFO tests.test_integration_fetch: Processing mock_backend...
2026-10-16 09:18:58,522 WARNING tests.test_integration_fetch: Skipping mock_backend due to stale data.
------------------------------ Captured log call -------------------------------
INFO     tests.test_integration_fetch:test_integration_fetch.py:174 Processing mock_backend...
WARNING  tests.test_integration_fetch:test_integration_fetch.py:182 Skipping mock_backend due to stale data.
=========================== short test summary info ============================
FAILED tests/test_integration_fetch.py::test_full_fetch_pipeline_with_save - AssertionError: At least one backend should have been processed and saved.
assert 0 > 0
========================= 1 failed, 5 passed in 1.13s ==========================



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
    - `code/process_raw.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_process_raw.py` — NOT invoked by the run-book
    - `code/tests/test_processed_csv.py` — NOT invoked by the run-book
    - `code/tests/test_stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
