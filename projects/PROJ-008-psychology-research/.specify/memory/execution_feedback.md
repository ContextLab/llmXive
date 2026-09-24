# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/descriptive_synthesis.py: synthetic/fake INPUT data not authorized by the spec — “…synthesis.     """     # Mock data for testing     class Mo…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/descriptive_synthesis.py: synthetic/fake INPUT data not authorized by the spec — “…synthesis.     """     # Mock data for testing     class Mo…”; 4 command(s) failed: python code/data/collector.py --start-year 2015 --end-year 2024 (rc=1); python code/data/cleaner.py --input data/raw/ --output data/processed/ (rc=1); python code/analysis/effect_sizes.py --input data/processed/clean_studies.csv --output data/processed/effect_sizes.csv (rc=1); 1 declared deliverable(s) absent: data/processed/cleaned_studies.csv

## Failing / missing run-book commands

- python code/data/collector.py --start-year 2015 --end-year 2024 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-008-psychology-research/code/data/collector.py", line 14, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/data/cleaner.py --input data/raw/ --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-008-psychology-research/code/data/cleaner.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/analysis/effect_sizes.py --input data/processed/clean_studies.csv --output data/processed/effect_sizes.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-008-psychology-research/code/analysis/effect_sizes.py", line 11, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --plots-dir viz/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-008-psychology-research/code/analysis/meta_analysis.py", line 6, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/processed/cleaned_studies.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_studies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/cleaner.py` — IS a run-book command
    - `code/data/verify_output.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/analysis/conditional_synthesis.py` — NOT invoked by the run-book
    - `code/analysis/effect_sizes.py` — IS a run-book command
    - `code/analysis/bias.py` — NOT invoked by the run-book
    - `code/analysis/meta_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_studies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
