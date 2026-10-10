# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/fetch_nrel_perovskites.py: synthetic/fake INPUT data not authorized by the spec — “…API key not found. Using mock data for demonstration.")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/fetch_nrel_perovskites.py: synthetic/fake INPUT data not authorized by the spec — “…API key not found. Using mock data for demonstration.")…”; 2 run-book script(s) missing (plan/impl path mismatch): python validation.py; python main.py; 4 command(s) failed: python code/data_ingestion.py (rc=1); python code/model_training.py (rc=1); python code/utils/state_manager.py (rc=1); 10 declared deliverable(s) absent: data/processed/descriptors_uncertainty.csv; data/processed/descriptors_v1.csv; data/processed/descriptors_vif_filtered.csv

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/data_ingestion.py", line 17, in <module>
    from merge_datasets import main as merge_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/merge_datasets.py", line 22, in <module>
    logging.FileHandler('data/raw/merge_operations.log')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/data/raw/merge_operations.log'

- python code/model_training.py -> rc=1

2026-10-10 03:28:44,465 - __main__ - INFO - Starting model training pipeline...
2026-10-10 03:28:44,467 - __main__ - ERROR - Data file data/processed/descriptors.csv not found. Run T017 first.

- python validation.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/validation.py': [Errno 2] No such file or directory

- python code/utils/state_manager.py -> rc=1
Usage: python -m code.utils.state_manager <update|verify> <file_path>


- python main.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v --cov=code -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/descriptors_uncertainty.csv
- data/processed/descriptors_v1.csv
- data/processed/descriptors_vif_filtered.csv
- data/processed/exclusion_log.csv
- data/processed/model_runs.json
- data/processed/vif_report.csv
- data/raw/metadata.json
- data/raw/mp_perovskites.csv
- data/raw/nrel_perovskites.csv
- data/raw/perovskites_merged.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptors_uncertainty.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/uncertainty_calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors_uncertainty.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors_v1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_vif_features.py` — NOT invoked by the run-book
    - `code/utils/vif_calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors_v1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors_vif_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_descriptors.py` — NOT invoked by the run-book
    - `code/filter_vif_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors_vif_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_descriptors.py` — NOT invoked by the run-book
    - `code/utils/uncertainty_calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_runs.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — IS a run-book command
    - `code/save_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_runs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_vif_features.py` — NOT invoked by the run-book
    - `code/utils/vif_calculator.py` — NOT invoked by the run-book
    - `code/vif_diagnostic.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/data_ingestion_metadata.py` — NOT invoked by the run-book
    - `code/extract_metadata.py` — NOT invoked by the run-book
    - `code/fetch_nrel_perovskites.py` — NOT invoked by the run-book
    - `code/filter_descriptors.py` — NOT invoked by the run-book
    - `code/filter_vif_features.py` — NOT invoked by the run-book
    - `code/grid_search.py` — NOT invoked by the run-book
    - `code/propagate_uncertainty.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/mp_perovskites.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/fetch_mp_perovskites.py` — NOT invoked by the run-book
    - `code/finalize_descriptors.py` — NOT invoked by the run-book
    - `code/merge_datasets.py` — NOT invoked by the run-book
    - `code/verify_dual_source.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/mp_perovskites.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/nrel_perovskites.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/fetch_nrel_perovskites.py` — NOT invoked by the run-book
    - `code/finalize_descriptors.py` — NOT invoked by the run-book
    - `code/merge_datasets.py` — NOT invoked by the run-book
    - `code/verify_dual_source.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/nrel_perovskites.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/perovskites_merged.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extract_metadata.py` — NOT invoked by the run-book
    - `code/finalize_descriptors.py` — NOT invoked by the run-book
    - `code/merge_datasets.py` — NOT invoked by the run-book
    - `code/utils/uncertainty_calculator.py` — NOT invoked by the run-book
    - `code/write_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/perovskites_merged.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
