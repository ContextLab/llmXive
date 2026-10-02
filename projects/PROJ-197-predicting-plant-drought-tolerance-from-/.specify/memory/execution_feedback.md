# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/compare.py: self-declared fabricated metric — “…ng("No CV scores found, using placeholder values")                 t_stat, p_…”
- code/models/compare.py: self-declared fabricated metric — “…results file not found, using placeholder values")             t_stat, p_valu…”
- code/config.py: synthetic/fake INPUT data not authorized by the spec — “…on Mode # If True: allow synthetic data fallback if real fetch f…”
- code/config.py: synthetic/fake INPUT data not authorized by the spec — “…Seed RANDOM_SEED = 42  # Synthetic Data Parameters SYNTHETIC_PAR…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…ipped (VALIDATION_MODE). Synthetic data will be used.")  def mai…”
- code/data/generate.py: synthetic/fake INPUT data not authorized by the spec — “…ta generation module for synthetic datasets and matrices.  This modu…”
- code/data/generate.py: synthetic/fake INPUT data not authorized by the spec — “…d matrices.  This module generates synthetic genomic features and phy…”
- code/data/generate.py: synthetic/fake INPUT data not authorized by the spec — “…es() -> str:     """     Generate synthetic genomic features and dro…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 21 fabricated/simulated-result signal(s) — results are not real measurements: code/models/compare.py: self-declared fabricated metric — “…ng("No CV scores found, using placeholder values")                 t_stat, p_…”; code/models/compare.py: self-declared fabricated metric — “…results file not found, using placeholder values")             t_stat, p_valu…”; code/config.py: synthetic/fake INPUT data not authorized by the spec — “…on Mode # If True: allow synthetic data fallback if real fetch f…”; 1 command(s) failed: python code/run_pipeline.py (rc=1); 2 declared deliverable(s) absent: data/logs/feature_importance.json; data/logs/metrics.json

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-197-predicting-plant-drought-tolerance-from-/code/run_pipeline.py", line 31, in <module>
    from data.download import download_try_data, fetch_ncbi_refseq, main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-197-predicting-plant-drought-tolerance-from-/code/data/download.py", line 20, in <module>
    logger = DataPipelineLog("download")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-197-predicting-plant-drought-tolerance-from-/code/utils/logging.py", line 24, in __init__
    ensure_directories([self.log_dir])
TypeError: ensure_directories() takes 0 positional arguments but 1 was given

## Declared deliverables still missing

- data/logs/feature_importance.json
- data/logs/metrics.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_directories` — defined in `code/config.py`; called 10 way(s):

- code/run_pipeline.py: ensure_directories()
- code/utils/logging.py: ensure_directories([self.log_dir])
- code/utils/metrics_logger.py: ensure_directories()
- code/models/compare.py: ensure_directories()
- code/models/evaluate.py: ensure_directories()
- code/models/train.py: ensure_directories()
- code/models/save_metrics_runner.py: ensure_directories(config)
- code/data/split.py: ensure_directories()
- code/data/ingest.py: ensure_directories()
- code/data/generate.py: ensure_directories()

Make `ensure_directories` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/feature_importance.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline.py` — IS a run-book command
    - `code/utils/metrics_logger.py` — NOT invoked by the run-book
    - `code/models/compare.py` — NOT invoked by the run-book
    - `code/models/entities.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/feature_importance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/logs/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pipeline.py` — IS a run-book command
    - `code/setup_directories.py` — NOT invoked by the run-book
    - `code/utils/metrics_logger.py` — NOT invoked by the run-book
    - `code/models/compare.py` — NOT invoked by the run-book
    - `code/models/evaluate.py` — NOT invoked by the run-book
    - `code/models/entities.py` — NOT invoked by the run-book
    - `code/models/save_metrics_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
