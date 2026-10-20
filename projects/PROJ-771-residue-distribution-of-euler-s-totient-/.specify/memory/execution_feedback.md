# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/stats.py: synthetic/fake INPUT data not authorized by the spec — “…arlo estimate with ``M`` simulated samples.     """     if seed is…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/stats.py: synthetic/fake INPUT data not authorized by the spec — “…arlo estimate with ``M`` simulated samples.     """     if seed is…”; 3 command(s) failed: python code/run_analysis.py --primes 3,5,7,11 --n 5000000 (rc=1); python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/ (rc=2)

## Failing / missing run-book commands

- python code/run_analysis.py --primes 3,5,7,11 --n 5000000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-771-residue-distribution-of-euler-s-totient-/code/run_analysis.py", line 29, in <module>
    from stats import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-771-residue-distribution-of-euler-s-totient-/code/stats.py", line 9, in <module>
    from exceptions import ResearchIncompleteError
ImportError: cannot import name 'ResearchIncompleteError' from 'exceptions' (/home/runner/work/llmXive/llmXive/projects/PROJ-771-residue-distribution-of-euler-s-totient-/code/exceptions.py)

- python -m pytest tests/unit/ -> rc=2
e/projects/PROJ-771-residue-distribution-of-euler-s-totient-/tests/unit/test_stats_t022.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_stats_t022.py:10: in <module>
    from stats import (
code/stats.py:9: in <module>
    from exceptions import ResearchIncompleteError
E   ImportError: cannot import name 'ResearchIncompleteError' from 'exceptions' (/home/runner/work/llmXive/llmXive/projects/PROJ-771-residue-distribution-of-euler-s-totient-/tests/unit/../../code/exceptions.py)
=========================== short test summary info ============================
ERROR tests/unit/test_run_analysis.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_stats_bootstrap.py
ERROR tests/unit/test_stats_fallback.py
ERROR tests/unit/test_stats_method.py
ERROR tests/unit/test_stats_save.py
ERROR tests/unit/test_stats_t022.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 0.25s ===============================


- python -m pytest tests/integration/ -> rc=2
module '/home/runner/work/llmXive/llmXive/projects/PROJ-771-residue-distribution-of-euler-s-totient-/tests/integration/test_t020_integration.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_t020_integration.py:11: in <module>
    from stats import run_block_bootstrap_deviation_test, run_full_statistical_analysis, save_statistical_result, StatisticalResult
code/stats.py:9: in <module>
    from exceptions import ResearchIncompleteError
E   ImportError: cannot import name 'ResearchIncompleteError' from 'exceptions' (/home/runner/work/llmXive/llmXive/projects/PROJ-771-residue-distribution-of-euler-s-totient-/code/exceptions.py)
=========================== short test summary info ============================
ERROR tests/integration/test_quickstart_validation.py
ERROR tests/integration/test_t020_integration.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.20s ===============================


