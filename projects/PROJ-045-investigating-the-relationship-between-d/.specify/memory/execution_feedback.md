# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/dft_runner.py: synthetic/fake INPUT data not authorized by the spec — “…ger(__name__)          # Mock data for demonstration     mo…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/dft_runner.py: synthetic/fake INPUT data not authorized by the spec — “…ger(__name__)          # Mock data for demonstration     mo…”; 5 command(s) failed: python code/download.py (rc=1); python code/validate.py (rc=1); python code/dft_runner.py --test-system Li7La3Zr2O12 (rc=1); 1 declared deliverable(s) absent: data/processed/analysis_results.json

## Failing / missing run-book commands

- python code/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/download.py", line 7, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/validate.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/dft_runner.py --test-system Li7La3Zr2O12 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/dft_runner.py", line 9, in <module>
    from pymatgen.core import Structure
ModuleNotFoundError: No module named 'pymatgen'
- python code/semi_empirical.py --all -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/semi_empirical.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-045-investigating-the-relationship-between-d/code/analysis.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/processed/analysis_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/semi_empirical.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
