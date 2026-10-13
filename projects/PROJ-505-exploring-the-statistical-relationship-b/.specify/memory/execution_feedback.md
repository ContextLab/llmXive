# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic solar‑wind / geomagnetic…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate deterministic synthetic solar‑wind and geomagnet…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…failed ({e}); generating synthetic data.")         # Generate sy…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…thetic data.")         # Generate synthetic aligned dataset directly…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”; code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”; code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic solar‑wind / geomagnetic…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/utils/verify_data.py --input data/processed/synthetic_aligned.parquet; 3 command(s) failed: python code/ingestion/generate_synthetic_data.py --output data/processed/synthetic_aligned.parquet (rc=1); python code/main.py (rc=1); python -m pytest tests/ (rc=2); 1 declared deliverable(s) absent: data/processed/synthetic_aligned.parquet

## Failing / missing run-book commands

- python code/ingestion/generate_synthetic_data.py --output data/processed/synthetic_aligned.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/generate_synthetic_data.py", line 16, in <module>
    from utils.io import save_parquet
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/__init__.py", line 9, in <module>
    from .io import compute_md5, verify_md5, load_parquet, save_parquet
ImportError: cannot import name 'compute_md5' from 'utils.io' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py)

- python code/utils/verify_data.py --input data/processed/synthetic_aligned.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/verify_data.py': [Errno 2] No such file or directory

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 8, in <module>
    from code.ingestion.download_ace import run_ingestion as run_ace_ingest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_ace.py", line 23, in <module>
    from code.utils.logging import DataIngestionError, get_logger, log_duration
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/__init__.py", line 9, in <module>
    from .io import compute_md5, verify_md5, load_parquet, save_parquet
ImportError: cannot import name 'compute_md5' from 'code.utils.io' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py)

- python -m pytest tests/ -> rc=2
t/test_synthetic.py:26: in <module>
    from code.ingestion.generate_synthetic_data import generate_solar_wind_composition
code/ingestion/generate_synthetic_data.py:16: in <module>
    from utils.io import save_parquet
utils/__init__.py:4: in <module>
    from .io import *
utils/io.py:4: in <module>
    from code.utils.io import (
E   ImportError: cannot import name 'compute_md5' from 'code.utils.io' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py)
=========================== short test summary info ============================
ERROR tests/integration/test_regression.py
ERROR tests/integration/test_sensitivity.py
ERROR tests/unit/test_coupling.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_download_ace.py
ERROR tests/unit/test_download_noaa.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_mkdirs.py
ERROR tests/unit/test_permutation.py
ERROR tests/unit/test_regression.py
ERROR tests/unit/test_synthetic.py
!!!!!!!!!!!!!!!!!!! Interrupted: 12 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 12 errors in 1.51s ==============================



## Declared deliverables still missing

- data/processed/synthetic_aligned.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/synthetic_aligned.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/generate_synthetic_data.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synthetic_aligned.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
