# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/preprocess_dMRI.py: synthetic/fake INPUT data not authorized by the spec — “…tion),         # we will generate a synthetic parcellation map if the…”
- code/data/preprocess_dMRI.py: synthetic/fake INPUT data not authorized by the spec — “…unner:         # We will generate a synthetic parcellation file to all…”
- code/data/quality_control.py: synthetic/fake INPUT data not authorized by the spec — “…annels with SNR < 5dB in simulated EEG data.  It calculates pipeline…”
- code/data/quality_control.py: synthetic/fake INPUT data not authorized by the spec — “…decibels (dB).      For simulated data, if no explicit noise ve…”
- code/data/quality_control.py: synthetic/fake INPUT data not authorized by the spec — “…re rigorous approach for simulated data:     If the simulator ou…”
- code/data/quality_control.py: synthetic/fake INPUT data not authorized by the spec — “…# Heuristic for simulated data without explicit noise s…”
- code/data/quality_control.py: synthetic/fake INPUT data not authorized by the spec — “…# Correct approach for simulated data QC:         # If the sim…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/data/preprocess_dMRI.py: synthetic/fake INPUT data not authorized by the spec — “…tion),         # we will generate a synthetic parcellation map if the…”; code/data/preprocess_dMRI.py: synthetic/fake INPUT data not authorized by the spec — “…unner:         # We will generate a synthetic parcellation file to all…”; code/data/quality_control.py: synthetic/fake INPUT data not authorized by the spec — “…annels with SNR < 5dB in simulated EEG data.  It calculates pipeline…”; 2 command(s) failed: python code/main.py (rc=1); python code/main.py --validate (rc=1)

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-472-investigating-the-impact-of-network-stru/code/main.py", line 16, in <module>
    from data.quality_control import calculate_pipeline_completeness
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-472-investigating-the-impact-of-network-stru/code/data/__init__.py", line 13, in <module>
    from .download import (
ModuleNotFoundError: No module named 'data.download'
- python code/main.py --validate -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-472-investigating-the-impact-of-network-stru/code/main.py", line 16, in <module>
    from data.quality_control import calculate_pipeline_completeness
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-472-investigating-the-impact-of-network-stru/code/data/__init__.py", line 13, in <module>
    from .download import (
ModuleNotFoundError: No module named 'data.download'
