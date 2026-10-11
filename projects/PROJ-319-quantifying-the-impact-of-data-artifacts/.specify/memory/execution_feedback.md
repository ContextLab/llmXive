# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…mages: int = 50):     """Generate synthetic planetary nebulae."""…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…t: Path):     """Process synthetic data by injecting artifacts a…”
- code/synthetic/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation and artifact…”
- code/synthetic/generator.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate N synthetic planetary nebulae with r…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: synthetic/fake INPUT data not authorized by the spec — “…mages: int = 50):     """Generate synthetic planetary nebulae."""…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…t: Path):     """Process synthetic data by injecting artifacts a…”; code/synthetic/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation and artifact…”; 7 command(s) failed: python code/main.py --mode generate --n-images 50 --output data/synthetic (rc=1); python code/main.py --mode process --input data/synthetic --output data/processed (rc=1); python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json (rc=1); 4 declared deliverable(s) absent: data/processed/calibration_functions.json; data/processed/noise_stats.csv; data/processed/run_manifest.json

## Failing / missing run-book commands

- python code/main.py --mode generate --n-images 50 --output data/synthetic -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py", line 36, in <module>
    from io.writer import write_run_manifest_for_pipeline
ModuleNotFoundError: No module named 'io.writer'; 'io' is not a package

- python code/main.py --mode process --input data/synthetic --output data/processed -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py", line 36, in <module>
    from io.writer import write_run_manifest_for_pipeline
ModuleNotFoundError: No module named 'io.writer'; 'io' is not a package

- python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py", line 36, in <module>
    from io.writer import write_run_manifest_for_pipeline
ModuleNotFoundError: No module named 'io.writer'; 'io' is not a package

- python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py", line 36, in <module>
    from io.writer import write_run_manifest_for_pipeline
ModuleNotFoundError: No module named 'io.writer'; 'io' is not a package

- python code/main.py --mode verify --output logs/verification.log -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py", line 36, in <module>
    from io.writer import write_run_manifest_for_pipeline
ModuleNotFoundError: No module named 'io.writer'; 'io' is not a package

- python -m pytest tests/unit/ -> rc=2
ckages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_statistical_tests.py:10: in <module>
    from analysis.statistical_tests import (
code/analysis/__init__.py:4: in <module>
    from .statistical_tests import perform_two_sample_ttest, apply_bonferroni_correction, run_noise_sweep_statistics, main
code/analysis/statistical_tests.py:12: in <module>
    from code.config import get_project_root, DATA_PROCESSED, NOISE_STATS_FILE, SATURATION_STATS_FILE
E   ImportError: cannot import name 'DATA_PROCESSED' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/config.py)
=========================== short test summary info ============================
ERROR tests/unit/test_artifacts.py
ERROR tests/unit/test_generator.py
ERROR tests/unit/test_power_analysis.py
ERROR tests/unit/test_statistical_tests.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.57s ===============================


- python -m pytest tests/contract/ -> rc=2
-data-artifacts/tests/contract/test_regression.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_regression.py:13: in <module>
    from code.analysis.statistical_tests import perform_two_sample_ttest
code/analysis/__init__.py:4: in <module>
    from .statistical_tests import perform_two_sample_ttest, apply_bonferroni_correction, run_noise_sweep_statistics, main
code/analysis/statistical_tests.py:12: in <module>
    from code.config import get_project_root, DATA_PROCESSED, NOISE_STATS_FILE, SATURATION_STATS_FILE
E   ImportError: cannot import name 'DATA_PROCESSED' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/config.py)
=========================== short test summary info ============================
ERROR tests/contract/test_regression.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.28s ===============================



## Declared deliverables still missing

- data/processed/calibration_functions.json
- data/processed/noise_stats.csv
- data/processed/run_manifest.json
- data/processed/saturation_stats.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/calibration_functions.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/regression.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/calibration_functions.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noise_stats.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/statistics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noise_stats.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/run_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/io/writer.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/run_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/saturation_stats.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/statistics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/saturation_stats.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
