# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate synthetic ACE data as a fallback."…”
- code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…warning("Falling back to synthetic ACE data generation.")     return…”
- code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic fallback data...")         df = load_s…”
- code/ingestion/download_noaa.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate synthetic NOAA data as a fallback.…”
- code/ingestion/download_noaa.py: synthetic/fake INPUT data not authorized by the spec — “…warning("Falling back to synthetic NOAA data generation.")     # Gene…”
- code/ingestion/download_noaa.py: synthetic/fake INPUT data not authorized by the spec — “…data generation.")     # Generate synthetic data for Kp and Dst…”
- code/ingestion/download_noaa.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic fallback data...")         df = load_s…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate synthetic ACE data as a fallback."…”; code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…warning("Falling back to synthetic ACE data generation.")     return…”; code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic fallback data...")         df = load_s…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/utils/verify_data.py --input data/processed/synthetic_aligned.parquet; 3 command(s) failed: python code/ingestion/generate_synthetic_data.py --output data/processed/synthetic_aligned.parquet (rc=1); python code/main.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python code/ingestion/generate_synthetic_data.py --output data/processed/synthetic_aligned.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/generate_synthetic_data.py", line 15, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/__init__.py", line 9, in <module>
    from .io import compute_md5, verify_md5, load_parquet, save_parquet
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py", line 10, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/.venv/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/utils/verify_data.py --input data/processed/synthetic_aligned.parquet -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/verify_data.py': [Errno 2] No such file or directory

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 12, in <module>
    from utils.logging import get_logger, setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/__init__.py", line 9, in <module>
    from .io import compute_md5, verify_md5, load_parquet, save_parquet
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py", line 10, in <module>
    import pyarrow.parquet as pq
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/.venv/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest tests/ -> rc=2
ition
code/ingestion/generate_synthetic_data.py:15: in <module>
    from utils.logging import get_logger
code/utils/__init__.py:9: in <module>
    from .io import compute_md5, verify_md5, load_parquet, save_parquet
code/utils/io.py:10: in <module>
    import pyarrow.parquet as pq
code/.venv/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/integration/test_regression.py
ERROR tests/integration/test_sensitivity.py
ERROR tests/unit/test_coupling.py
ERROR tests/unit/test_download_ace.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_io.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_mkdirs.py
ERROR tests/unit/test_permutation.py
ERROR tests/unit/test_regression.py
ERROR tests/unit/test_synthetic.py
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 11 errors in 0.99s ==============================


