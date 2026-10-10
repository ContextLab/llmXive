# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.main --input data/processed/subgraph.parquet --output data/processed/subgraph_with_clusters.parquet (rc=1); python -m tests.contract.test_schemas (rc=1); python -m pytest tests/unit/test_embeddings.py::test_novelty_independence (rc=4); 3 declared deliverable(s) absent: data/processed/excluded_nodes.json; data/processed/final_analysis_dataset.parquet; data/processed/subgraph_with_clusters.parquet

## Failing / missing run-book commands

- python -m src.cli.main --input data/processed/subgraph.parquet --output data/processed/subgraph_with_clusters.parquet -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/.venv/bin/python: No module named src.cli.main

- python -m tests.contract.test_schemas -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/tests/contract/test_schemas.py", line 15, in <module>
    from src.lib import config
ModuleNotFoundError: No module named 'src.lib'

- python -m pytest tests/unit/test_embeddings.py::test_novelty_independence -> rc=4
 1 error

==================================== ERRORS ====================================
________________ ERROR collecting tests/unit/test_embeddings.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/tests/unit/test_embeddings.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
code/tests/unit/test_embeddings.py:16: in <module>
    from src.services.embeddings import (
E   ModuleNotFoundError: No module named 'src.services.embeddings'
=========================== short test summary info ============================
ERROR code/tests/unit/test_embeddings.py
=============================== 1 error in 0.08s ===============================

ERROR: found no collectors for /home/runner/work/llmXive/llmXive/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code/tests/unit/test_embeddings.py::test_novelty_independence



## Declared deliverables still missing

- data/processed/excluded_nodes.json
- data/processed/final_analysis_dataset.parquet
- data/processed/subgraph_with_clusters.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/excluded_nodes.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_novelty_calculation.py` — NOT invoked by the run-book
    - `code/src/services/embeddings.py` — NOT invoked by the run-book
    - `code/tests/integration/test_embeddings_pipeline.py` — NOT invoked by the run-book
    - `code/tests/unit/test_embeddings.py` — NOT invoked by the run-book
    - `code/tests/unit/test_embeddings_service.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/excluded_nodes.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_analysis_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_novelty_calculation.py` — NOT invoked by the run-book
    - `code/scripts/run_validation.py` — NOT invoked by the run-book
    - `code/scripts/save_final_dataset.py` — NOT invoked by the run-book
    - `code/scripts/save_statistical_metrics.py` — NOT invoked by the run-book
    - `code/tests/integration/test_final_dataset.py` — NOT invoked by the run-book
    - `code/tests/integration/test_statistical_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_analysis_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/subgraph_with_clusters.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_novelty_calculation.py` — NOT invoked by the run-book
    - `code/scripts/run_validation.py` — NOT invoked by the run-book
    - `code/scripts/save_final_dataset.py` — NOT invoked by the run-book
    - `code/scripts/save_graph_pipeline.py` — NOT invoked by the run-book
    - `code/src/cli/main.py` — NOT invoked by the run-book
    - `code/src/services/embeddings.py` — NOT invoked by the run-book
    - `code/src/services/ingest.py` — NOT invoked by the run-book
    - `code/src/services/save_graph.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/subgraph_with_clusters.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
