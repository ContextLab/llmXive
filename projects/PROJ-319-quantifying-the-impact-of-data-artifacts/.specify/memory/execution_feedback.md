# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/sensitivity_sweep.py: synthetic/fake INPUT data not authorized by the spec — “…=SEED)     logger.info(f"Generated base synthetic nebula with shape {base_…”
- code/analysis/statistical_tests.py: synthetic/fake INPUT data not authorized by the spec — “…e} not found. Generating synthetic clean data for demonstration (FAILS…”
- code/synthetic/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation and artifact…”
- code/synthetic/generator.py: synthetic/fake INPUT data not authorized by the spec — “…etary Nebula Generator.  Generates synthetic planetary nebulae with k…”
- code/synthetic/generator.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic planetary nebula image a…”
- code/synthetic/generator.py: synthetic/fake INPUT data not authorized by the spec — “…# For our synthetic data, we define the center as…”
- code/synthetic/generator.py: synthetic/fake INPUT data not authorized by the spec — “…Main entry point to generate synthetic data and ground truth me…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/sensitivity_sweep.py: synthetic/fake INPUT data not authorized by the spec — “…=SEED)     logger.info(f"Generated base synthetic nebula with shape {base_…”; code/analysis/statistical_tests.py: synthetic/fake INPUT data not authorized by the spec — “…e} not found. Generating synthetic clean data for demonstration (FAILS…”; code/synthetic/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation and artifact…”; 5 run-book script(s) missing (plan/impl path mismatch): python code/main.py --mode generate --n-images 50 --output data/synthetic; python code/main.py --mode process --input data/synthetic --output data/processed; python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json; 1 declared deliverable(s) absent: data/processed/saturation_sweep.csv

## Failing / missing run-book commands

- python code/main.py --mode generate --n-images 50 --output data/synthetic -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py': [Errno 2] No such file or directory
- python code/main.py --mode process --input data/synthetic --output data/processed -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py': [Errno 2] No such file or directory
- python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py': [Errno 2] No such file or directory
- python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py': [Errno 2] No such file or directory
- python code/main.py --mode verify --output logs/verification.log -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-319-quantifying-the-impact-of-data-artifacts/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/saturation_sweep.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/saturation_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/synthetic/artifacts.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/analysis/statistical_tests.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/saturation_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
