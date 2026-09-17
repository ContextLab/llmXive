# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/services/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…, preventing fallback to synthetic data."""     pass  def _calcu…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/services/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…, preventing fallback to synthetic data."""     pass  def _calcu…”; 9 command(s) failed: python code/main.py (rc=1); python code/services/data_ingestion.py (rc=1); python code/services/anxiety_scoring.py (rc=1); 7 declared deliverable(s) absent: data/processed/correlation_plot.png; data/processed/coverage_report.json; data/processed/final_analysis.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/main.py", line 18, in <module>
    from code.config import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/config.py", line 11, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/services/data_ingestion.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/services/data_ingestion.py", line 8, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/services/anxiety_scoring.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/services/anxiety_scoring.py", line 6, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/services/proxy_extractor.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/services/proxy_extractor.py", line 12, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/analysis/statistical_test.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/analysis/statistical_test.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/viz/plot_results.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/viz/plot_results.py", line 5, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'
- python code/profiling.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/profiling.py", line 10, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/profiling.py --check-only -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/profiling.py", line 10, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/profiling.py --output data/processed/custom_report.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-281-the-impact-of-perceived-control-over-dig/code/profiling.py", line 10, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/correlation_plot.png
- data/processed/coverage_report.json
- data/processed/final_analysis.csv
- data/processed/preprocessed_text.csv
- data/processed/proxy_results.csv
- data/processed/scoring_results.csv
- data/raw/social_media.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz/save_visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/coverage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/services/coverage_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/coverage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/profiling.py` — IS a run-book command
    - `code/services/__init__.py` — NOT invoked by the run-book
    - `code/services/merge_and_save.py` — NOT invoked by the run-book
    - `code/viz/plot_results.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/preprocessed_text.csv` is declared but was NOT written. Scripts referencing it:
    - `code/services/anxiety_scoring.py` — IS a run-book command
    - `code/services/coverage_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/preprocessed_text.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/proxy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/services/__init__.py` — NOT invoked by the run-book
    - `code/services/proxy_extractor.py` — IS a run-book command
    - `code/services/merge_and_save.py` — NOT invoked by the run-book
    - `code/services/proxy_saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/proxy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scoring_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/services/__init__.py` — NOT invoked by the run-book
    - `code/services/scoring_saver.py` — NOT invoked by the run-book
    - `code/services/merge_and_save.py` — NOT invoked by the run-book
    - `code/services/coverage_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scoring_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/social_media.csv` is declared but was NOT written. Scripts referencing it:
    - `code/profiling.py` — IS a run-book command
    - `code/services/data_ingestion.py` — IS a run-book command
    - `code/services/anxiety_scoring.py` — IS a run-book command
    - `code/services/proxy_extractor.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/social_media.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
