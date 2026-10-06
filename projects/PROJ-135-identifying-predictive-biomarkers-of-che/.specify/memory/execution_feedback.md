# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/utils.py: self-declared fabricated metric — “…synthetic data or fallback to mock values.     If the file does not ex…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/utils.py: self-declared fabricated metric — “…synthetic data or fallback to mock values.     If the file does not ex…”; 2 run-book script(s) missing (plan/impl path mismatch): python src/meta_analysis.py; python src/loo_controller.py; 3 command(s) failed: python src/data_acquisition.py --mode real --subset-size (rc=1); python src/preprocessing.py (rc=1); python code/src/differential_expression.py (rc=1)

## Failing / missing run-book commands

- python src/data_acquisition.py --mode real --subset-size -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/data_acquisition.py", line 16, in <module>
    from src.utils import calculate_checksum, setup_logging, update_state_artifact_hashes
ImportError: cannot import name 'update_state_artifact_hashes' from 'src.utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/utils.py)
- python src/preprocessing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/preprocessing.py", line 19, in <module>
    from src.utils import setup_logging, ensure_path_exists
ImportError: cannot import name 'ensure_path_exists' from 'src.utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/utils.py)
- python code/src/differential_expression.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/src/differential_expression.py", line 9, in <module>
    from .config import get_project_root, ensure_directories
ImportError: attempted relative import with no known parent package
- python src/meta_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/meta_analysis.py': [Errno 2] No such file or directory
- python src/loo_controller.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-135-identifying-predictive-biomarkers-of-che/src/loo_controller.py': [Errno 2] No such file or directory
