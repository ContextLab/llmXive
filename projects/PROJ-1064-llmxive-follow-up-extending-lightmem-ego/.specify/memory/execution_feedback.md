# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/cli/run.py --mode validation; 1 command(s) failed: python src/data/download.py --output-dir data/raw/ (rc=1); 11 declared deliverable(s) absent: data/processed/faiss_index_mapping.json; data/processed/memory_nodes.parquet; data/processed/validation_queries.json

## Failing / missing run-book commands

- python src/data/download.py --output-dir data/raw/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/download.py", line 9, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/cli/run.py --mode validation -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/cli/run.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/faiss_index_mapping.json
- data/processed/memory_nodes.parquet
- data/processed/validation_queries.json
- data/results/evaluation_metrics.json
- data/results/evaluation_queries.json
- data/results/evaluation_report.json
- data/results/mcnemar_test.json
- data/results/optimal_parameters.json
- data/results/validation_run.json
- figures/latency_vs_age.png
- figures/long_term_accuracy.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/faiss_index_mapping.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/memory_nodes.parquet` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/validation_queries.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_metrics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_queries.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_report.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/mcnemar_test.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/optimal_parameters.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/validation_run.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/latency_vs_age.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/long_term_accuracy.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
