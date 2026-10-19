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

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”; code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”; code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic solar‑wind / geomagnetic…”; 5 command(s) failed: python code/ingestion/download_real.py --start 2000-01-01 --end 2020-12-31 (rc=1); python code/ingestion/download_real.py --start 2000-01-01 --end 2000-12-31 (rc=1); python -m code.main (rc=1); 1 declared deliverable(s) absent: data/processed/aligned_hourly.parquet

## Failing / missing run-book commands

- python code/ingestion/download_real.py --start 2000-01-01 --end 2020-12-31 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_real.py", line 20, in <module>
    import pyspedas.cdaweb as cdaweb  # Unified CDAWeb downloader
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'pyspedas.cdaweb'

- python code/ingestion/download_real.py --start 2000-01-01 --end 2000-12-31 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_real.py", line 20, in <module>
    import pyspedas.cdaweb as cdaweb  # Unified CDAWeb downloader
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'pyspedas.cdaweb'

- python -m code.main -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 11, in <module>
    from code.ingestion.align import align_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/align.py", line 15, in <module>
    from utils.logging import AlignmentError, get_logger, log_duration, check_memory_usage
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/utils/__init__.py", line 4, in <module>
    from .io import *
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/utils/io.py", line 4, in <module>
    from code.utils.io import (
ImportError: cannot import name 'compute_md5' from 'code.utils.io' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py)

- python -m code.main --quick -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 11, in <module>
    from code.ingestion.align import align_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/align.py", line 15, in <module>
    from utils.logging import AlignmentError, get_logger, log_duration, check_memory_usage
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/utils/__init__.py", line 4, in <module>
    from .io import *
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/utils/io.py", line 4, in <module>
    from code.utils.io import (
ImportError: cannot import name 'compute_md5' from 'code.utils.io' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/io.py)

- python -m pytest tests/ -> rc=2
atplotlib/_fontconfig_pattern.py:89
../../.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:89
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/lib/python3.11/site-packages/matplotlib/_mathtext.py:45
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_download_real.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 14 warnings, 1 error in 2.27s =========================



## Declared deliverables still missing

- data/processed/aligned_hourly.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_hourly.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/align.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_hourly.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
