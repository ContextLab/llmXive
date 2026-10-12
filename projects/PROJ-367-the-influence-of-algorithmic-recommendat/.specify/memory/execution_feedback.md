# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset mimicking user-a…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…s:         pd.DataFrame: Generated synthetic dataset     """     rand…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…(f"Generated {n_samples} synthetic records saved to {output_path}")…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main entry point for synthetic data generation."""     # Loa…”
- code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…taset()     logger.info("Synthetic data generation complete")  i…”
- code/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…s script assumes: 1. The synthetic dataset exists at `data/raw/synt…”
- code/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…clean state, though for synthetic data it's static.         # T…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset mimicking user-a…”; code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…s:         pd.DataFrame: Generated synthetic dataset     """     rand…”; code/data_generation.py: synthetic/fake INPUT data not authorized by the spec — “…(f"Generated {n_samples} synthetic records saved to {output_path}")…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/preprocessing.py; 5 command(s) failed: python code/data_fetcher.py (rc=1); python code/main.py (rc=1); python -m pytest tests/unit/ -v (rc=2); 1 declared deliverable(s) absent: data/processed/cleaned_data.parquet

## Failing / missing run-book commands

- python code/data_fetcher.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/data_fetcher.py", line 19, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/preprocessing.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/preprocessing.py': [Errno 2] No such file or directory

- python code/main.py -> rc=1
llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/main.py", line 23, in <module>
    from ingestion import DataSchemaError, validate_schema, load_project_data, ingest_and_save
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/ingestion.py", line 6, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest tests/unit/ -v -> rc=2
taset
../../.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/__init__.py:17: in <module>
    from .arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
ERROR tests/unit/test_data_fetcher.py
ERROR tests/unit/test_data_generation.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_merger.py
ERROR tests/unit/test_sensitivity.py
ERROR tests/unit/test_validate_real_data.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 2.20s ===============================


- python -m pytest tests/integration/ -v -> rc=2
tegration/test_pipeline.py:20: in <module>
    from ingestion import validate_schema, ingest_and_clean
code/ingestion.py:6: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/__init__.py:17: in <module>
    from .arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/integration/test_main_verification.py
ERROR tests/integration/test_pipeline.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.26s ===============================


- python -m pytest tests/contract/ -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-367-the-influence-of-algorithmic-recommendat/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-367-the-influence-of-algorithmic-recommendat
configfile: pytest.ini
plugins: platformdirs-4.13.0, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/



## Declared deliverables still missing

- data/processed/cleaned_data.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_fetcher.py` — IS a run-book command
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/merger.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
