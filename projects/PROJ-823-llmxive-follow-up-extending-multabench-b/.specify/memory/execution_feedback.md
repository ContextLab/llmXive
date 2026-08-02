# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/pipelines/run_optimized_pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…xecution time based on a mock dataset size.         # In a rea…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/pipelines/run_optimized_pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…xecution time based on a mock dataset size.         # In a rea…”; 4 command(s) failed: python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8 (rc=1); python code/pipelines/run_conditioned.py --seed --epochs 15 (rc=1); python code/pipelines/run_analysis.py (rc=1); 4 declared deliverable(s) absent: data/artifacts/data_integrity_report.json; data/artifacts/gpu_tuned_baselines.csv; data/artifacts/runtime_report.json

## Failing / missing run-book commands

- python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_baseline.py", line 16, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/pipelines/run_conditioned.py --seed --epochs 15 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_conditioned.py", line 8, in <module>
    from models.trainer import create_trainer, Trainer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/__init__.py", line 4, in <module>
    from models.base import BaseModel, FrozenEmbeddingModel, ProjectionModel
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/base.py", line 13, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/pipelines/run_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_analysis.py", line 27, in <module>
    from analysis.correlation_analysis import main as correlation_analysis_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/analysis/correlation_analysis.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/pipelines/update_state.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/update_state.py", line 12, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/artifacts/data_integrity_report.json
- data/artifacts/gpu_tuned_baselines.csv
- data/artifacts/runtime_report.json
- data/processed/metadata_stats_summary.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/data_integrity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/verify_data_integrity.py` — NOT invoked by the run-book
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/data_integrity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/gpu_tuned_baselines.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/run_t_test.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/run_analysis.py` — IS a run-book command
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/gpu_tuned_baselines.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/runtime_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/runtime_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata_stats_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/pipelines/verify_data_integrity.py` — NOT invoked by the run-book
    - `code/pipelines/run_integration_test.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/run_analysis.py` — IS a run-book command
    - `code/pipelines/run_correlation_analysis.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata_stats_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
