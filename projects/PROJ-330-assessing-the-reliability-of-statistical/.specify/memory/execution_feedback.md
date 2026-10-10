# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/validate_quickstart.py: self-declared fabricated metric — “…ta)             logger.info(f"Mock metric calculation result: {result}"…”
- code/scripts/validate_quickstart.py: self-declared fabricated metric — “…e:             logger.error(f"Mock metric calculation failed: {e}")…”
- code/scripts/validate_quickstart.py: self-declared fabricated metric — “…)             return False, f"Mock metric calculation failed: {e}"…”
- code/src/permutation.py: self-declared fabricated metric — “…# Simulate result for placeholder         results.append({"iteration": i, "sta…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/validate_quickstart.py: self-declared fabricated metric — “…ta)             logger.info(f"Mock metric calculation result: {result}"…”; code/scripts/validate_quickstart.py: self-declared fabricated metric — “…e:             logger.error(f"Mock metric calculation failed: {e}")…”; code/scripts/validate_quickstart.py: self-declared fabricated metric — “…)             return False, f"Mock metric calculation failed: {e}"…”; 5 command(s) failed: python code/main.py --dataset GSE12345 (rc=1); python code/main.py --analysis stability --dataset GSE12345 (rc=1); python code/main.py --analysis permutation --dataset GSE12345 --iterations 1000 (rc=1)

## Failing / missing run-book commands

- python -c "from src.data_loader import create_default_manifest; create_default_manifest()" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/data_loader.py", line 36, in <module>
    def load_manifest(manifest_path: Optional[Path] = None) -> dict:
                                     ^^^^^^^^
NameError: name 'Optional' is not defined

- python -c "from src.data_loader import fetch_dataset; fetch_dataset('GSE12345')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/data_loader.py", line 36, in <module>
    def load_manifest(manifest_path: Optional[Path] = None) -> dict:
                                     ^^^^^^^^
NameError: name 'Optional' is not defined

- python code/main.py --dataset GSE12345 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/main.py", line 12, in <module>
    from src.data_loader import fetch_dataset, load_manifest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/data_loader.py", line 36, in <module>
    def load_manifest(manifest_path: Optional[Path] = None) -> dict:
                                     ^^^^^^^^
NameError: name 'Optional' is not defined

- python code/main.py --analysis stability --dataset GSE12345 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/main.py", line 12, in <module>
    from src.data_loader import fetch_dataset, load_manifest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/data_loader.py", line 36, in <module>
    def load_manifest(manifest_path: Optional[Path] = None) -> dict:
                                     ^^^^^^^^
NameError: name 'Optional' is not defined

- python code/main.py --analysis permutation --dataset GSE12345 --iterations 1000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/main.py", line 12, in <module>
    from src.data_loader import fetch_dataset, load_manifest
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/data_loader.py", line 36, in <module>
    def load_manifest(manifest_path: Optional[Path] = None) -> dict:
                                     ^^^^^^^^
NameError: name 'Optional' is not defined

- python code/scripts/generate_cross_dataset_visualization.py -> rc=1
ability_results.json
2026-10-10 07:28:57,835 - __main__ - WARNING - Results file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/data/aggregated_stability_results.json. This is expected if no datasets have been processed yet. Generating placeholder visualization.
2026-10-10 07:28:57,835 - __main__ - INFO - Generating cross-dataset comparison visualization...
2026-10-10 07:28:57,835 - __main__ - ERROR - Error generating visualization: ensure_directories() takes 0 positional arguments but 1 was given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/scripts/generate_cross_dataset_visualization.py", line 87, in main
    output_path = generate_cross_dataset_comparison(results, output_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/report.py", line 144, in generate_cross_dataset_comparison
    ensure_directories(output_path)
TypeError: ensure_directories() takes 0 positional arguments but 1 was given

- python -m pytest code/tests/ -> rc=2
st_r_config.py _________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/tests/test_r_config.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
code/tests/test_r_config.py:11: in <module>
    from src.r_config import (
E   ImportError: cannot import name 'load_r_config' from 'src.r_config' (/home/runner/work/llmXive/llmXive/projects/PROJ-330-assessing-the-reliability-of-statistical/code/src/r_config.py)
=========================== short test summary info ============================
ERROR code/tests/test_data_loader.py - NameError: name 'Optional' is not defined
ERROR code/tests/test_permutation.py - NameError: name 'pd' is not defined
ERROR code/tests/test_r_config.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.28s ===============================


