# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/model_comparison.py: self-declared fabricated metric — “…MODE: {run_mode}")          # Mock results for demonstration (in real f…”
- code/data/simulation_stories.py: function `generate_story_text` returns a bare RNG draw (line 43) — a reported value computed from no real input
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…Load MFQ data from the generated synthetic dataset or real source.…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…al Stories data from the generated synthetic dataset.     """     dat…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…nteraction logs from the generated synthetic dataset.     """     dat…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…s implementation assumes synthetic data is available as per the…”
- code/data/simulation_mfq.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic MFQ data based on Gervai…”
- code/data/simulation_mfq.py: synthetic/fake INPUT data not authorized by the spec — “…s:         pd.DataFrame: Synthetic MFQ data with columns:…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/model_comparison.py: self-declared fabricated metric — “…MODE: {run_mode}")          # Mock results for demonstration (in real f…”; code/data/simulation_stories.py: function `generate_story_text` returns a bare RNG draw (line 43) — a reported value computed from no real input; code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…Load MFQ data from the generated synthetic dataset or real source.…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/data/simulation.py; 7 command(s) failed: python code/data/ingest.py (rc=1); python code/data/preprocess.py (rc=1); python code/models/bayesian.py (rc=1)

## Failing / missing run-book commands

- python code/data/ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/ingest.py", line 4, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/data/simulation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/simulation.py': [Errno 2] No such file or directory
- python code/data/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/preprocess.py", line 19, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/models/bayesian.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian.py", line 8, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/model_comparison.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/model_comparison.py", line 6, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/validation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/validation.py", line 6, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/utils/hashing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/hashing.py", line 12, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/reports/generate_report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/reports/generate_report.py", line 14, in <module>
    from config import ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/config.py", line 4, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
