# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…berately lightweight: it generates simple synthetic PNG images (solid colour…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…berately lightweight: it generates simple synthetic PNG images (solid colour…”; 4 command(s) failed: python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 (rc=1); python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ (rc=1); python -m pytest -q tests/contract (rc=4)

## Failing / missing run-book commands

- python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 -> rc=1

Error processing validation file: "Successful validation record missing session identifier: {'figure_id': '0', 'vector_match': True, 'semantic_pass': True, 'similarity_score': 1.0}"

- python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ -> rc=1

2026-10-17 02:39:35,541 ERROR __main__: Validation records missing required columns: {'interface', 'time_to_success_ms', 'iteration_count', 'participant_id'}

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


- python -m src.run_pipeline --config config.yaml -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/src/run_pipeline.py", line 22, in <module>
    from src.run_pipeline import seed_all  # type: ignore  # will be defined below
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/src/run_pipeline.py", line 22, in <module>
    from src.run_pipeline import seed_all  # type: ignore  # will be defined below
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'seed_all' from partially initialized module 'src.run_pipeline' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/src/run_pipeline.py)

