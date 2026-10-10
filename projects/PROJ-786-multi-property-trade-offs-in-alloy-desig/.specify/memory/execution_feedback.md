# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/model_training.py: self-declared fabricated metric — “…shear'],             'note': "Placeholder values. Actual per-point variance t…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/model_training.py: self-declared fabricated metric — “…shear'],             'note': "Placeholder values. Actual per-point variance t…”; 7 run-book script(s) missing (plan/impl path mismatch): python ingestion/load_oqmd.py; python ingestion/encode_composition.py; python modeling/train_surrogates.py; 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/ (rc=2); 6 declared deliverable(s) absent: data/processed/encoded_alloys.csv; data/processed/loso_test_points.csv; data/processed/model_validation_report.json

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/main.py", line 19, in <module>
    from model_training import run_training_pipeline, generate_validation_report, save_validation_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/model_training.py", line 20, in <module>
    from models.alloy_entry import AlloyEntry
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/models/__init__.py", line 4, in <module>
    from .alloy_entry import AlloyEntry, ElementDescriptor
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/models/alloy_entry.py", line 2, in <module>
    from pydantic import BaseModel, Field, model_validator
ImportError: cannot import name 'model_validator' from 'pydantic' (/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/lib/python3.11/site-packages/pydantic/__init__.cpython-311-x86_64-linux-gnu.so)

- python ingestion/load_oqmd.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/ingestion/load_oqmd.py': [Errno 2] No such file or directory

- python ingestion/encode_composition.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/ingestion/encode_composition.py': [Errno 2] No such file or directory

- python modeling/train_surrogates.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/modeling/train_surrogates.py': [Errno 2] No such file or directory

- python analysis/feasibility_check.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/analysis/feasibility_check.py': [Errno 2] No such file or directory

- python analysis/clustering.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/analysis/clustering.py': [Errno 2] No such file or directory

- python analysis/sensitivity.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/analysis/sensitivity.py': [Errno 2] No such file or directory

- python modeling/pareto_optimize.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/modeling/pareto_optimize.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
d Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_versioning_verification.py:16: in <module>
    from versioning import (
E   ImportError: cannot import name 'DEFAULT_STATE_FILE' from 'versioning' (/home/runner/work/llmXive/llmXive/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/code/versioning.py)
=========================== short test summary info ============================
ERROR tests/contract/test_cluster_variance_flag.py
ERROR tests/contract/test_model_output.py
ERROR tests/integration/test_loso_uncertainty_integration.py
ERROR tests/unit/test_alloy_entry.py
ERROR tests/unit/test_cluster_analysis.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_feature_encoder_validation.py
ERROR tests/unit/test_feature_validation.py
ERROR tests/unit/test_loso_cv.py
ERROR tests/unit/test_sensitivity_analysis.py
ERROR tests/unit/test_versioning_verification.py
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 11 errors in 1.37s ==============================



## Declared deliverables still missing

- data/processed/encoded_alloys.csv
- data/processed/loso_test_points.csv
- data/processed/model_validation_report.json
- data/processed/sensitivity_analysis.csv
- data/results/pareto_frontier.csv
- data/results/robustness_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/encoded_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cluster_analysis.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/feature_encoder.py` — NOT invoked by the run-book
    - `code/metrics_calculation.py` — NOT invoked by the run-book
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/pareto_optimization.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/encoded_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/loso_test_points.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/loso_test_points.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/model_validation.py` — NOT invoked by the run-book
    - `code/pareto_optimization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cluster_analysis.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/robustness_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pareto_frontier.csv` is declared but was NOT written. Scripts referencing it:
    - `code/metrics_calculation.py` — NOT invoked by the run-book
    - `code/pareto_optimization.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/pareto_frontier.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/robustness_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/robustness_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/robustness_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
