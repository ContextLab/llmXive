# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/runtime_validator.py: synthetic/fake INPUT data not authorized by the spec — “…> list:     """Generates mock data for a dry run."""     re…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/runtime_validator.py: synthetic/fake INPUT data not authorized by the spec — “…> list:     """Generates mock data for a dry run."""     re…”; 2 command(s) failed: python code/data_pipeline.py --sample-size --seed 42 (rc=1); python code/statistical_analysis.py (rc=1)

## Failing / missing run-book commands

- python code/data_pipeline.py --sample-size --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/data_pipeline.py", line 22, in <module>
    logger = setup_logging("data_pipeline")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: setup_logging() takes 0 positional arguments but 1 was given
- python code/statistical_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py", line 15, in <module>
    logger = setup_logging(__name__)
             ^^^^^^^^^^^^^^^^^^^^^^^
TypeError: setup_logging() takes 0 positional arguments but 1 was given

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logging` — defined in `code/config.py`; called 14 way(s):

- code/linting_runner.py: logger = setup_logging(__name__)
- code/quickstart_validator.py: logger = setup_logging("quickstart_validator", logging.INFO)
- code/data_pipeline.py: logger = setup_logging("data_pipeline")
- code/verify_results.py: setup_logging()
- code/run_quickstart_validation.py: setup_logging()
- code/validate_baseline.py: setup_logging()
- code/linting_config.py: setup_logging()
- code/semantic_analysis.py: setup_logging()
- code/runtime_validator.py: setup_logging()
- code/vif_report_generator.py: logger = setup_logging(__name__)
- code/generate_run_metadata.py: logger = setup_logging(__name__)
- code/statistical_analysis.py: logger = setup_logging(__name__)
- code/runtime_verification.py: setup_logging()
- code/run_pipeline_validation.py: setup_logging()

Make `setup_logging` in `code/config.py` accept ALL of the above.
