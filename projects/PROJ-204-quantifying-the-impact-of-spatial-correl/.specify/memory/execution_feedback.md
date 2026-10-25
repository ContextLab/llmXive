# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/models.py: synthetic/fake INPUT data not authorized by the spec — “…erformance]:     """     Generate synthetic performance records for…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/models.py: synthetic/fake INPUT data not authorized by the spec — “…erformance]:     """     Generate synthetic performance records for…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/data/download_feasibility.py; 5 command(s) failed: python code/main_pipeline.py (rc=1); python -m pytest tests/unit/test_spatial_metrics.py -v (rc=2); python -m pytest tests/unit/test_diffusion_length.py -v (rc=4); 3 declared deliverable(s) absent: data/processed/spatial_metrics.csv; data/processed/unified_dataset.csv; data/results/ingestion_stats.json

## Failing / missing run-book commands

- python code/data/download_feasibility.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-204-quantifying-the-impact-of-spatial-correl/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl/code/data/download_feasibility.py': [Errno 2] No such file or directory

- python code/main_pipeline.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl/code/main_pipeline.py", line 20, in <module>
    from data.ingest import ingest_and_filter_dataset
ModuleNotFoundError: No module named 'data.ingest'

- python -m pytest tests/unit/test_spatial_metrics.py -v -> rc=2
ootstrap._gcd_import(name[level:], package, level)
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
tests/unit/test_spatial_metrics.py:14: in <module>
    from analysis.spatial_metrics import (
code/analysis/spatial_metrics.py:24: in <module>
    from analysis.spatial_metrics import (
E   ImportError: cannot import name 'compute_autocorrelation' from partially initialized module 'analysis.spatial_metrics' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl/code/analysis/spatial_metrics.py)
=========================== short test summary info ============================
ERROR tests/unit/test_spatial_metrics.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.50s ===============================


- python -m pytest tests/unit/test_diffusion_length.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-204-quantifying-the-impact-of-spatial-correl/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl
configfile: pyproject.toml
plugins: platformdirs-4.13.5, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_diffusion_length.py


- python -m pytest tests/unit/test_robustness.py -v -> rc=1
terable

code/analysis/robustness.py:58: TypeError
=========================== short test summary info ============================
FAILED tests/unit/test_robustness.py::TestCalculateCorrelation::test_calculate_correlation_pearson - TypeError: calculate_correlation() got an unexpected keyword argument 'method'
FAILED tests/unit/test_robustness.py::TestCalculateCorrelation::test_calculate_correlation_spearman - TypeError: calculate_correlation() got an unexpected keyword argument 'method'
FAILED tests/unit/test_robustness.py::TestPerformLeaveOneOutCV::test_loo_cv_returns_dataframe - TypeError: 'builtin_function_or_method' object is not iterable
FAILED tests/unit/test_robustness.py::TestPerformLeaveOneOutCV::test_loo_cv_delta_r_positive - TypeError: 'builtin_function_or_method' object is not iterable
FAILED tests/unit/test_robustness.py::TestPerformLeaveOneOutCV::test_loo_cv_max_delta_r - TypeError: 'builtin_function_or_method' object is not iterable
FAILED tests/unit/test_robustness.py::TestPerformLeaveOneOutCV::test_loo_cv_small_dataset - TypeError: 'builtin_function_or_method' object is not iterable
============================== 6 failed in 0.58s ===============================


- python -m pytest tests/integration/test_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-204-quantifying-the-impact-of-spatial-correl/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl
configfile: pyproject.toml
plugins: platformdirs-4.13.5, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_pipeline.py



## Declared deliverables still missing

- data/processed/spatial_metrics.csv
- data/processed/unified_dataset.csv
- data/results/ingestion_stats.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/spatial_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/spatial_metrics.py` — NOT invoked by the run-book
    - `code/main_pipeline.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/spatial_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unified_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/validation/co_location.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/ingestion_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/main_pipeline.py` — IS a run-book command
    - `code/report/generate.py` — NOT invoked by the run-book
    - `code/utils/ingestion_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ingestion_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
