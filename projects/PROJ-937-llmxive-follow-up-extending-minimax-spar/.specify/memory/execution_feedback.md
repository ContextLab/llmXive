# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/mini_max_wrapper.py: self-declared fabricated metric — “…r implementation that returns dummy scores.         In a full implement…”
- code/data/ruler_loader.py: synthetic/fake INPUT data not authorized by the spec — “…Optional import yaml  # Mock dataset for MVP if real download…”
- code/data/ruler_loader.py: synthetic/fake INPUT data not authorized by the spec — “…For this MVP, returns a mock dataset if real download is not…”
- code/data/ruler_loader.py: synthetic/fake INPUT data not authorized by the spec — “…For T012, we return the mock data to ensure the script run…”
- code/eval/statistical.py: synthetic/fake INPUT data not authorized by the spec — “…1, 0.05, 0.1]          # Mock data for API verification onl…”
- code/heuristics/block_entropy.py: synthetic/fake INPUT data not authorized by the spec — “…nfig, logger)          # Generate synthetic attention scores for tes…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/models/mini_max_wrapper.py: self-declared fabricated metric — “…r implementation that returns dummy scores.         In a full implement…”; code/data/ruler_loader.py: synthetic/fake INPUT data not authorized by the spec — “…Optional import yaml  # Mock dataset for MVP if real download…”; code/data/ruler_loader.py: synthetic/fake INPUT data not authorized by the spec — “…For this MVP, returns a mock dataset if real download is not…”; 3 command(s) failed: python code/main.py --action download (rc=1); python code/main.py --action run --heuristic all --threshold 0.05 (rc=1); python code/main.py --action analyze (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/main.py", line 17, in <module>
    from data.loader import download_and_verify_ruler, verify_ruler_data_integrity
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/data/__init__.py", line 12, in <module>
    from .preprocess import (
ImportError: cannot import name 'check_memory_pressure' from 'data.preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/data/preprocess.py)

- python code/main.py --action run --heuristic all --threshold 0.05 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/main.py", line 17, in <module>
    from data.loader import download_and_verify_ruler, verify_ruler_data_integrity
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/data/__init__.py", line 12, in <module>
    from .preprocess import (
ImportError: cannot import name 'check_memory_pressure' from 'data.preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/data/preprocess.py)

- python code/main.py --action analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/main.py", line 17, in <module>
    from data.loader import download_and_verify_ruler, verify_ruler_data_integrity
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/data/__init__.py", line 12, in <module>
    from .preprocess import (
ImportError: cannot import name 'check_memory_pressure' from 'data.preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/data/preprocess.py)

