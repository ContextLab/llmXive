# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…er.info("Falling back to synthetic data generation.")         re…”
- code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…str) -> str:     """     Generate a deterministic synthetic dataset mimicking the Om…”
- code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with {NUM_SYNTHETIC_SEQU…”
- code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…)          logger.info(f"Synthetic dataset generated at: {output_pa…”
- code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…zip.          # We will generate synthetic data as the fallback is…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…f"Neither real nor synthetic dataset found. "…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…er.info("Falling back to synthetic data generation.")         re…”; code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…str) -> str:     """     Generate a deterministic synthetic dataset mimicking the Om…”; code/data/dataset_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with {NUM_SYNTHETIC_SEQU…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --run-all; python code/main.py --step ingest; python code/main.py --step solve; 1 command(s) failed: python -m pytest tests/ -v (rc=2); 3 declared deliverable(s) absent: data/processed/filtered_sequences.csv; data/processed/poses_estimated.json; data/processed/reconstruction_results.csv

## Failing / missing run-book commands

- python code/main.py --run-all -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step ingest -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step solve -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step analyze -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
ed 0 items / 1 error

==================================== ERRORS ====================================
_ ERROR collecting projects/PROJ-853-llmxive-follow-up-extending-omnidirector/tests/unit/test_config.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/tests/unit/test_config.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_config.py:14: in <module>
    from config import (
E   ImportError: cannot import name 'DEFAULT_CONSTANTS' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-853-llmxive-follow-up-extending-omnidirector/code/config.py)
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.28s ===============================



## Declared deliverables still missing

- data/processed/filtered_sequences.csv
- data/processed/poses_estimated.json
- data/processed/reconstruction_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_sequences.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/results_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/scoring.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/data/writer.py` — NOT invoked by the run-book
    - `code/geometry/pose_writer.py` — NOT invoked by the run-book
    - `code/geometry/solver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_sequences.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/poses_estimated.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/results_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/geometry/pose_writer.py` — NOT invoked by the run-book
    - `code/geometry/reconstruction.py` — NOT invoked by the run-book
    - `code/geometry/solver.py` — NOT invoked by the run-book
    - `code/geometry/writer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/poses_estimated.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/reconstruction_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/results_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/scoring.py` — NOT invoked by the run-book
    - `code/analysis/timing.py` — NOT invoked by the run-book
    - `code/tests/unit/test_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/reconstruction_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
