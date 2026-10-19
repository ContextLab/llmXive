# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_gap_resolver.py: synthetic/fake INPUT data not authorized by the spec — “…g files are genuine, non‑synthetic data that satisfy the “Real D…”
- code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…d:         logger.error("Synthetic data detected in raw director…”
- code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…alDataValidationError if synthetic data is detected.     """…”
- code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…ealDataValidationError(f"Synthetic data detected in file: {data_…”
- code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…ealDataValidationError(f"Synthetic data detected in directory: {…”
- code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…result['message'] = 'Synthetic data detected'             re…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/data_gap_resolver.py: synthetic/fake INPUT data not authorized by the spec — “…g files are genuine, non‑synthetic data that satisfy the “Real D…”; code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…d:         logger.error("Synthetic data detected in raw director…”; code/validators.py: synthetic/fake INPUT data not authorized by the spec — “…alDataValidationError if synthetic data is detected.     """…”; 2 command(s) failed: python code/main.py (rc=1); python -m pytest -v tests/ (rc=2)

## Failing / missing run-book commands

- python code/main.py -> rc=1
8:11:49,171 - __main__ - INFO - Summary report saved to /home/runner/work/llmXive/llmXive/projects/PROJ-168-statistical-evaluation-of-dimensionality/results/summary.json
2026-10-19 18:11:49,171 - __main__ - INFO - Launching Snakemake workflow in FIXED_EFFECTS mode...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-168-statistical-evaluation-of-dimensionality/bin/snakemake", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-168-statistical-evaluation-of-dimensionality/lib/python3.11/site-packages/snakemake/__init__.py", line 2736, in main
    parser = get_argument_parser()
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-168-statistical-evaluation-of-dimensionality/lib/python3.11/site-packages/snakemake/__init__.py", line 1607, in get_argument_parser
    lp_solvers = pulp.list_solvers(onlyAvailable=True)
                 ^^^^^^^^^^^^^^^^^
AttributeError: module 'pulp' has no attribute 'list_solvers'. Did you mean: 'listSolvers'?
2026-10-19 18:11:49,332 - __main__ - ERROR - Pipeline execution failed with exit code 1

- python -m pytest -v tests/ -> rc=2

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_clustering.py - FileNotFoundError: [Errno 2] No such file or...
ERROR tests/test_embeddings.py
ERROR tests/test_generate_requirements.py
ERROR tests/test_geometry.py
ERROR tests/test_validators.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
======================= 21 warnings, 5 errors in 21.54s ========================


## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
