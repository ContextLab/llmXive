# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…JSON file.     Triggers synthetic data generation if no valid p…”
- code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…amples found. Triggering synthetic data generation (T005).")…”
- code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…ain()             print("Synthetic data generation completed.")…”
- code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…print(f"Error generating synthetic data: {e}")             raise…”
- code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…real data and failed to generate synthetic data.")          return…”
- code/01_ingest.py: synthetic/fake INPUT data not authorized by the spec — “…on‑the‑fly using the     synthetic data generator (T005 logic).…”
- code/01_ingest.py: synthetic/fake INPUT data not authorized by the spec — “…W_DATA_PATH}. Generating synthetic dataset...")         # The gener…”
- code/01_ingest.py: synthetic/fake INPUT data not authorized by the spec — “…Error(                 f"Synthetic data generation failed to cre…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 fabricated/simulated-result signal(s) — results are not real measurements: code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…JSON file.     Triggers synthetic data generation if no valid p…”; code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…amples found. Triggering synthetic data generation (T005).")…”; code/00_query_sources.py: synthetic/fake INPUT data not authorized by the spec — “…ain()             print("Synthetic data generation completed.")…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 2 command(s) failed: python code/01_ingest.py (rc=1); python code/03_train.py (rc=1); 3 declared deliverable(s) absent: data/processed/merged_dataset.csv; data/results/data_validation_report.json; data/results/model_metrics.json

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/main.py': [Errno 2] No such file or directory
- python code/01_ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/01_ingest.py", line 25, in <module>
    from utils.config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/utils/__init__.py", line 8, in <module>
    from .config import ConfigError, ProjectConfig, get_config, reset_config, EnvConfig, EnvConfigError
ImportError: cannot import name 'EnvConfig' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/utils/config.py)
- python code/03_train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/03_train.py", line 21, in <module>
    from utils.imputation import impute_missing_values
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/utils/__init__.py", line 8, in <module>
    from .config import ConfigError, ProjectConfig, get_config, reset_config, EnvConfig, EnvConfigError
ImportError: cannot import name 'EnvConfig' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-339-predicting-plant-volatile-organic-compou/code/utils/config.py)

## Declared deliverables still missing

- data/processed/merged_dataset.csv
- data/results/data_validation_report.json
- data/results/model_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest.py` — IS a run-book command
    - `code/03_aggregate.py` — NOT invoked by the run-book
    - `code/05_validate_stability.py` — NOT invoked by the run-book
    - `code/02_merge.py` — NOT invoked by the run-book
    - `code/03_train.py` — IS a run-book command
    - `code/05_validate.py` — NOT invoked by the run-book
    - `code/04_interpret.py` — NOT invoked by the run-book
    - `code/utils/env_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/data_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest.py` — IS a run-book command
    - `code/05_validate.py` — NOT invoked by the run-book
    - `code/utils/env_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/data_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_train.py` — IS a run-book command
    - `code/06_generate_report.py` — NOT invoked by the run-book
    - `code/utils/env_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
