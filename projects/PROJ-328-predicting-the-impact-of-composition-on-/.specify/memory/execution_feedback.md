# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/generate_validation_report.py: synthetic/fake INPUT data not authorized by the spec — “…isk. It must not rely on synthetic data or mock inputs. It expec…”
- code/ingestion/generate_validation_report.py: synthetic/fake INPUT data not authorized by the spec — “…ely on synthetic data or mock inputs. It expects real inputs…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/generate_validation_report.py: synthetic/fake INPUT data not authorized by the spec — “…isk. It must not rely on synthetic data or mock inputs. It expec…”; code/ingestion/generate_validation_report.py: synthetic/fake INPUT data not authorized by the spec — “…ely on synthetic data or mock inputs. It expects real inputs…”; 1 command(s) failed: python code/run_pipeline.py (rc=1); 7 declared deliverable(s) absent: data/processed/.ingestion_status.json; data/processed/clr_features.csv; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=1
edicting-the-impact-of-composition-on-/code/ingestion/cleaner.py", line 16, in <module>
    from config import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-328-predicting-the-impact-of-composition-on-/code/config.py", line 13, in <module>
    from utils.error_handlers import ConfigurationError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-328-predicting-the-impact-of-composition-on-/code/utils/__init__.py", line 6, in <module>
    from .helpers import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-328-predicting-the-impact-of-composition-on-/code/utils/helpers.py", line 11, in <module>
    from config import get_composition_sum_threshold, get_max_elements
ImportError: cannot import name 'get_composition_sum_threshold' from partially initialized module 'config' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-328-predicting-the-impact-of-composition-on-/code/config.py)

2026-10-11 02:30:15,865 - __main__ - CRITICAL - Critical step T013: Data Cleaner failed. Stopping pipeline.
2026-10-11 02:30:15,865 - __main__ - ERROR - Pipeline failed. Failed steps: ['T012d-Execute: Literature Scraper', 'T013: Data Cleaner']



## Declared deliverables still missing

- data/processed/.ingestion_status.json
- data/processed/clr_features.csv
- data/processed/descriptors.csv
- data/processed/predictions.csv
- data/processed/solder_hardness_cleaned.csv
- data/raw/.ingestion_status.json
- data/raw/api_fetched.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/.ingestion_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/add_power_limitation_warning.py` — NOT invoked by the run-book
    - `code/evaluation/generate_report.py` — NOT invoked by the run-book
    - `code/ingestion/aggregate_final_report.py` — NOT invoked by the run-book
    - `code/ingestion/aggregator.py` — NOT invoked by the run-book
    - `code/ingestion/cleaner.py` — NOT invoked by the run-book
    - `code/ingestion/generate_validation_report.py` — NOT invoked by the run-book
    - `code/ingestion/pipeline_runner.py` — NOT invoked by the run-book
    - `code/ingestion/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/.ingestion_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/clr_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features/transformer.py` — NOT invoked by the run-book
    - `code/ingestion/verify_task_ordering.py` — NOT invoked by the run-book
    - `code/models/xgboost_trainer.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/clr_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/bootstrap.py` — NOT invoked by the run-book
    - `code/evaluation/sensitivity.py` — NOT invoked by the run-book
    - `code/features/collinearity.py` — NOT invoked by the run-book
    - `code/features/descriptor_engine.py` — NOT invoked by the run-book
    - `code/features/descriptor_engine_main.py` — NOT invoked by the run-book
    - `code/ingestion/verify_task_ordering.py` — NOT invoked by the run-book
    - `code/models/entities.py` — NOT invoked by the run-book
    - `code/models/linear_trainer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/bootstrap.py` — NOT invoked by the run-book
    - `code/evaluation/model_comparison.py` — NOT invoked by the run-book
    - `code/visualization/pdp.py` — NOT invoked by the run-book
    - `code/visualization/plot_saver.py` — NOT invoked by the run-book
    - `code/visualization/scatter.py` — NOT invoked by the run-book
    - `code/visualization/sensitivity_plot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/solder_hardness_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/bootstrap.py` — NOT invoked by the run-book
    - `code/features/descriptor_engine.py` — NOT invoked by the run-book
    - `code/features/transformer.py` — NOT invoked by the run-book
    - `code/ingestion/cleaner.py` — NOT invoked by the run-book
    - `code/ingestion/pipeline_runner.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/ingestion/verify_task_ordering.py` — NOT invoked by the run-book
    - `code/models/linear_trainer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/solder_hardness_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/.ingestion_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/add_power_limitation_warning.py` — NOT invoked by the run-book
    - `code/evaluation/generate_report.py` — NOT invoked by the run-book
    - `code/ingestion/aggregate_final_report.py` — NOT invoked by the run-book
    - `code/ingestion/aggregator.py` — NOT invoked by the run-book
    - `code/ingestion/cleaner.py` — NOT invoked by the run-book
    - `code/ingestion/generate_validation_report.py` — NOT invoked by the run-book
    - `code/ingestion/pipeline_runner.py` — NOT invoked by the run-book
    - `code/ingestion/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/.ingestion_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/api_fetched.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/aggregator.py` — NOT invoked by the run-book
    - `code/ingestion/api_fetcher.py` — NOT invoked by the run-book
    - `code/ingestion/validation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/api_fetched.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
