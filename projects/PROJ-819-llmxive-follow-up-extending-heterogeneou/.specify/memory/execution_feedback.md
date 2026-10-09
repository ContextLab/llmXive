# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: function `generate_random_float` returns a bare RNG draw (line 26) — a reported value computed from no real input
- code/data/generator.py: function `generate_random_int` returns a bare RNG draw (line 31) — a reported value computed from no real input
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…generator.py  Implements synthetic data generation for the llmXi…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…> Dict[str, Any]:     """Generate a single synthetic query object."""     # G…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: function `generate_random_float` returns a bare RNG draw (line 26) — a reported value computed from no real input; code/data/generator.py: function `generate_random_int` returns a bare RNG draw (line 31) — a reported value computed from no real input; code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…generator.py  Implements synthetic data generation for the llmXi…”; 6 command(s) failed: python -m code.pipeline.runner --mode baseline --input data/derived/queries.json --output data/derived/results_baseline.csv (rc=1); python -m code.pipeline.runner --mode cached --threshold 0.90 --input data/derived/queries.json --output data/derived/results_0.90.csv (rc=1); python -m code.pipeline.runner --mode cached --threshold 0.95 --input data/derived/queries.json --output data/derived/results_0.95.csv (rc=1)

## Failing / missing run-book commands

- python -m code.pipeline.runner --mode baseline --input data/derived/queries.json --output data/derived/results_baseline.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/pipeline/runner.py", line 12, in <module>
    from data.loaders import load_test_set, load_warmup_set
ModuleNotFoundError: No module named 'data.loaders'

- python -m code.pipeline.runner --mode cached --threshold 0.90 --input data/derived/queries.json --output data/derived/results_0.90.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/pipeline/runner.py", line 12, in <module>
    from data.loaders import load_test_set, load_warmup_set
ModuleNotFoundError: No module named 'data.loaders'

- python -m code.pipeline.runner --mode cached --threshold 0.95 --input data/derived/queries.json --output data/derived/results_0.95.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/pipeline/runner.py", line 12, in <module>
    from data.loaders import load_test_set, load_warmup_set
ModuleNotFoundError: No module named 'data.loaders'

- python -m code.pipeline.runner --mode cached --threshold 0.99 --input data/derived/queries.json --output data/derived/results_0.99.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/pipeline/runner.py", line 12, in <module>
    from data.loaders import load_test_set, load_warmup_set
ModuleNotFoundError: No module named 'data.loaders'

- python -m code.analysis.visualization --input data/derived/results_*.csv --output figures/trade-off-curve.png -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/.venv/bin/python: No module named code.analysis.visualization

- python -m code.analysis.stats --input data/derived/results_*.csv --output reports/statistical_significance.json -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/code/.venv/bin/python: No module named code.analysis.stats

