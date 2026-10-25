# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/report.py: synthetic/fake INPUT data not authorized by the spec — “…analysis.     """     # Mock data for direct execution tes…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/report.py: synthetic/fake INPUT data not authorized by the spec — “…analysis.     """     # Mock data for direct execution tes…”; 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/unit/ (rc=2); 2 declared deliverable(s) absent: data/processed/metrics.csv; data/processed/report.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
rk/llmXive/llmXive/.llmxive-venvs/PROJ-425-predicting-molecular-complexity-using-in/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-425-predicting-molecular-complexity-using-in/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-425-predicting-molecular-complexity-using-in/code/main.py", line 13, in <module>
    from download import fetch_molecules, load_and_sample_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-425-predicting-molecular-complexity-using-in/code/download.py", line 29, in <module>
    raise ImportError("The 'datasets' package is required. Install via: pip install datasets")
ImportError: The 'datasets' package is required. Install via: pip install datasets

- python -m pytest tests/unit/ -> rc=2
    import pyarrow as pa
../../.llmxive-venvs/PROJ-425-predicting-molecular-complexity-using-in/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_download.py:23: in <module>
    from code.download import (
code/download.py:29: in <module>
    raise ImportError("The 'datasets' package is required. Install via: pip install datasets")
E   ImportError: The 'datasets' package is required. Install via: pip install datasets
=========================== short test summary info ============================
ERROR tests/unit/test_analysis.py
ERROR tests/unit/test_download.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.56s ===============================



## Declared deliverables still missing

- data/processed/metrics.csv
- data/processed/report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/report.py` — NOT invoked by the run-book
    - `code/setup_env.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
