# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv`
  - script usage: `graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUTPUT] [--out OUT]`
  - argparse error: `graph_builder.py: error: unrecognized arguments: --backend ibmq_manila`
- run-book command: `python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv`
  - script usage: `graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUTPUT] [--out OUT]`
  - argparse error: `graph_builder.py: error: unrecognized arguments: --backend ibmq_manila`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m pytest tests/test_graph_builder.py -v (rc=1); python -m pytest tests/test_stats_engine.py -v (rc=2); python -m pytest tests/test_integration_fetch.py -v   # live API (rate‑limited) (rc=4); 3 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/graph_metrics.csv; data/processed/performance_metrics.csv

## Failing / missing run-book commands

- python -m pytest tests/test_graph_builder.py -v -> rc=1
-
configfile: pyproject.toml
collecting ... collected 3 items

tests/test_graph_builder.py::test_build_coupling_graph PASSED            [ 33%]
tests/test_graph_builder.py::test_compute_shortest_path_metrics_path_graph PASSED [ 66%]
tests/test_graph_builder.py::test_compute_edge_betweenness_and_spectral_gap_disconnected FAILED [100%]

=================================== FAILURES ===================================
_________ test_compute_edge_betweenness_and_spectral_gap_disconnected __________
tests/test_graph_builder.py:39: in test_compute_edge_betweenness_and_spectral_gap_disconnected
    assert pytest.approx(metrics["edge_betweenness_mean"], rel=1e-6) == 1.0
E   assert 0.16666666666666666 ± 1.7e-07 == 1.0
E     
E     comparison failed
E     Obtained: 1.0
E     Expected: 0.16666666666666666 ± 1.7e-07
=========================== short test summary info ============================
FAILED tests/test_graph_builder.py::test_compute_edge_betweenness_and_spectral_gap_disconnected - assert 0.16666666666666666 ± 1.7e-07 == 1.0
  
  comparison failed
  Obtained: 1.0
  Expected: 0.16666666666666666 ± 1.7e-07
========================= 1 failed, 2 passed in 0.27s ==========================


- python -m pytest tests/test_stats_engine.py -v -> rc=2
1-6f1866971868/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/test_stats_engine.py:26: in <module>
    from stats_engine import (
E   ImportError: cannot import name 'robustness_check_time_window' from 'stats_engine' (/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/stats_engine.py)
=========================== short test summary info ============================
ERROR tests/test_stats_engine.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.92s ===============================


- python -m pytest tests/test_integration_fetch.py -v   # live API (rate‑limited) -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-163-exploring-the-role-of-network-structure-/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv -> rc=2

usage: graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUTPUT] [--out OUT]
                        [--generate-metrics]
graph_builder.py: error: unrecognized arguments: --backend ibmq_manila

- python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv -> rc=2

usage: graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUTPUT] [--out OUT]
                        [--generate-metrics]
graph_builder.py: error: unrecognized arguments: --backend ibmq_manila


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
    - `code/graph_builder.py` — IS a run-book command
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
