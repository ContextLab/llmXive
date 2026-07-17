# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/viz/plots.py: synthetic/fake INPUT data not authorized by the spec — “…# 3. Coefficient Plot (Simulated data if model output not stri…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis/robustness.py`
  - script usage: `robustness.py [-h] --data DATA [--formula FORMULA]`
  - argparse error: `robustness.py: error: the following arguments are required: --data`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/viz/plots.py: synthetic/fake INPUT data not authorized by the spec — “…# 3. Coefficient Plot (Simulated data if model output not stri…”; 5 run-book script(s) missing (plan/impl path mismatch): python code/ingestion.py; python code/preprocessing.py; python code/modeling.py; 1 command(s) failed: python code/analysis/robustness.py (rc=2); 1 declared deliverable(s) absent: data/processed/merged_sample.parquet

## Failing / missing run-book commands

- python code/ingestion.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/ingestion.py': [Errno 2] No such file or directory
- python code/preprocessing.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/preprocessing.py': [Errno 2] No such file or directory
- python code/modeling.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/modeling.py': [Errno 2] No such file or directory
- python code/analysis/robustness.py -> rc=2
    usage: robustness.py [-h] --data DATA [--formula FORMULA]
                     [--random-effect RANDOM_EFFECT] [--weights WEIGHTS]
                     [--bootstrap-iterations BOOTSTRAP_ITERATIONS]
                     [--output-dir OUTPUT_DIR] [--n-jobs N_JOBS]
robustness.py: error: the following arguments are required: --data
- python code/viz.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/viz.py': [Errno 2] No such file or directory
- python code/verify_reproducibility.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-020-the-use-of-climate-smart-agricultural-pr/code/verify_reproducibility.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/merged_sample.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/validation/quickstart_validator.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/data/features.py` — NOT invoked by the run-book
    - `code/analysis/performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
