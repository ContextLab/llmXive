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
/utils/io.py", line 33, in save_parquet
    df.to_parquet(file_path, index=False, engine="pyarrow")
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/util/_decorators.py", line 333, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 3113, in to_parquet
    return to_parquet(
           ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 476, in to_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 78, in get_engine
    return PyArrowImpl()
           ^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 163, in __init__
    import_optional_dependency(
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/_optional.py", line 138, in import_optional_dependency
    raise ImportError(msg)
ImportError: Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.

- python code/utils/verify_data.py --input data/processed/synthetic_aligned.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/verify_data.py': [Errno 2] No such file or directory

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 17, in <module>
    from code.analysis.integrate_results import integrate_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/analysis/integrate_results.py", line 36, in <module>
    def create_coefficients_dataframe(regression_data: Dict[str, Any]) -> pd.DataFrame:
                                                                          ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python -m pytest tests/ -> rc=2
========================== ERRORS ====================================
_ ERROR collecting projects/PROJ-505-exploring-the-statistical-relationship-b/tests/integration/test_sensitivity.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/tests/integration/test_sensitivity.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_sensitivity.py:20: in <module>
    from analysis.sensitivity import (
E   ImportError: cannot import name 'load_regression_results' from 'analysis.sensitivity' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/analysis/sensitivity.py)
=========================== short test summary info ============================
ERROR tests/integration/test_sensitivity.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.34s ===============================



## Declared deliverables still missing

- data/processed/synthetic_aligned.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/synthetic_aligned.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/generate_synthetic_data.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synthetic_aligned.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
