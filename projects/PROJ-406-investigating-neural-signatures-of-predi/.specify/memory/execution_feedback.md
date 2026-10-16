# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.ingest.load_illusions  --download  --output-dir data/raw (rc=1); python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean (rc=1); python -m src.model.predictive_coding  --input data/clean/clean_muller_lyer.csv  --output data/derived/precision_parameters.csv  --seed 42 (rc=1); 9 declared deliverable(s) absent: data/clean/aligned_subjects.csv; data/clean/clean_muller_lyer.csv; data/clean/clean_ponzo.csv

## Failing / missing run-book commands

- python -m src.ingest.load_illusions  --download  --output-dir data/raw -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 44, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 44, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.model.predictive_coding  --input data/clean/clean_muller_lyer.csv  --output data/derived/precision_parameters.csv  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: No module named src.model.predictive_coding

- python -m src.analysis.null_model  --input data/clean/clean_ponzo.csv  --output data/derived/ponzo_susceptibility.csv  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: No module named src.analysis.null_model

- python -m src.analysis.correlation  --precision data/derived/precision_parameters.csv  --susceptibility data/derived/ponzo_susceptibility.csv  --results outputs/correlation_results.json  --fig-dir outputs/figures  --bootstrap 1000  --permute 1000  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: No module named src.analysis.correlation


## Declared deliverables still missing

- data/clean/aligned_subjects.csv
- data/clean/clean_muller_lyer.csv
- data/clean/clean_ponzo.csv
- data/derived/ponzo_null_parameters.csv
- data/derived/ponzo_susceptibility.csv
- data/derived/precision_parameters.csv
- data/merged/merged_results.csv
- data/raw/muller_lyer.parquet
- data/raw/ponzo.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/clean/aligned_subjects.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/clean/clean_muller_lyer.csv` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/clean/clean_muller_lyer.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/clean/clean_ponzo.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/ponzo_null_parameters.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/ponzo_susceptibility.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/precision_parameters.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/merged/merged_results.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/raw/muller_lyer.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/muller_lyer.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ponzo.parquet` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
