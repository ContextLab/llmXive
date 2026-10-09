# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/generation/generation_profile.py: synthetic/fake INPUT data not authorized by the spec — “…t[str, Any]:     """     Generate a synthetic token sequence for profi…”
- code/src/generation/generation_profile.py: synthetic/fake INPUT data not authorized by the spec — “…alloc.start()          # Generate synthetic data for profiling     l…”
- code/src/generation/generation_profile.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic data: {num_batches} batches o…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/data/download.py --task gsm8k --limit 500`
  - script usage: `download.py [-h] [--max-samples MAX_SAMPLES] [--gsm8k-path GSM8K_PATH]`
  - argparse error: `download.py: error: unrecognized arguments: --task gsm8k --limit 500`
- run-book command: `python code/src/data/download.py --task minigrid --limit 500`
  - script usage: `download.py [-h] [--max-samples MAX_SAMPLES] [--gsm8k-path GSM8K_PATH]`
  - argparse error: `download.py: error: unrecognized arguments: --task minigrid --limit 500`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/generation/generation_profile.py: synthetic/fake INPUT data not authorized by the spec — “…t[str, Any]:     """     Generate a synthetic token sequence for profi…”; code/src/generation/generation_profile.py: synthetic/fake INPUT data not authorized by the spec — “…alloc.start()          # Generate synthetic data for profiling     l…”; code/src/generation/generation_profile.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic data: {num_batches} batches o…”; 2 run-book script(s) missing (plan/impl path mismatch): bash scripts/setup.sh; python code/src/analysis/regression.py --input data/processed/gsm8k_entropy.jsonl data/processed/minigrid_entropy.jsonl --output data/results/regression_results.json; 5 command(s) failed: python code/src/data/download.py --task gsm8k --limit 500 (rc=2); python code/src/data/download.py --task minigrid --limit 500 (rc=2); python code/src/generation/generation.py --model Qwen/Qwen1.5-0.5B --task gsm8k --output data/processed/gsm8k_labels.jsonl (rc=1)

## Failing / missing run-book commands

- bash scripts/setup.sh -> rc=-1

shell script must be an existing project-local .sh file
- python code/src/data/download.py --task gsm8k --limit 500 -> rc=2

usage: download.py [-h] [--max-samples MAX_SAMPLES] [--gsm8k-path GSM8K_PATH]
                   [--minigrid-path MINIGRID_PATH]
download.py: error: unrecognized arguments: --task gsm8k --limit 500

- python code/src/data/download.py --task minigrid --limit 500 -> rc=2

usage: download.py [-h] [--max-samples MAX_SAMPLES] [--gsm8k-path GSM8K_PATH]
                   [--minigrid-path MINIGRID_PATH]
download.py: error: unrecognized arguments: --task minigrid --limit 500

- python code/src/generation/generation.py --model Qwen/Qwen1.5-0.5B --task gsm8k --output data/processed/gsm8k_labels.jsonl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py", line 65, in <module>
    logger = setup_logging()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py", line 33, in setup_logging
    handler = logging.handlers.RotatingFileHandler(
              ^^^^^^^^^^^^^^^^
AttributeError: module 'logging' has no attribute 'handlers'. Did you mean: '_handlers'?

- python code/src/generation/generation.py --model Qwen/Qwen1.5-0.5B --task minigrid --output data/processed/minigrid_labels.jsonl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py", line 65, in <module>
    logger = setup_logging()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/generation/generation.py", line 33, in setup_logging
    handler = logging.handlers.RotatingFileHandler(
              ^^^^^^^^^^^^^^^^
AttributeError: module 'logging' has no attribute 'handlers'. Did you mean: '_handlers'?

- python code/src/analysis/regression.py --input data/processed/gsm8k_entropy.jsonl data/processed/minigrid_entropy.jsonl --output data/results/regression_results.json -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/analysis/regression.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
models/api.py:76: in <module>
    from . import datasets, distributions, iolib, regression, robust, tools
code/.venv/lib/python3.11/site-packages/statsmodels/distributions/__init__.py:7: in <module>
    from .discrete import (
code/.venv/lib/python3.11/site-packages/statsmodels/distributions/discrete.py:5: in <module>
    from scipy._lib._util import _lazywhere
E   ImportError: cannot import name '_lazywhere' from 'scipy._lib._util' (/home/runner/work/llmXive/llmXive/projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/.venv/lib/python3.11/site-packages/scipy/_lib/_util.py)
=========================== short test summary info ============================
ERROR tests/integration/test_entropy_extraction.py - AttributeError: module '...
ERROR tests/integration/test_generation_t014.py - AttributeError: module 'log...
ERROR tests/integration/test_ground_truth_labeling.py - AttributeError: modul...
ERROR tests/unit/test_generation.py - AttributeError: module 'logging' has no...
ERROR tests/unit/test_logistic_model.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 1.54s ===============================


