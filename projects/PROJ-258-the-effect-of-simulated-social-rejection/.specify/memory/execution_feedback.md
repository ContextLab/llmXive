# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…subject directories with dummy data     # In real implementa…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…subject directories with dummy data     # In real implementa…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json; 2 command(s) failed: python code/preprocess.py --input data/raw --output data/processed/analysis_ready.csv (rc=1); python code/report.py --input results/analysis_output.json --output paper/report.md (rc=1)

## Failing / missing run-book commands

- python code/preprocess.py --input data/raw --output data/processed/analysis_ready.csv -> rc=1
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1645, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1904, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '--input'
- python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/analyze.py': [Errno 2] No such file or directory
- python code/report.py --input results/analysis_output.json --output paper/report.md -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 192, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 189, in main
    run_reporting_pipeline(analysis_path, report_path, final_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 156, in run_reporting_pipeline
    with open(analysis_results_path, 'r') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '--input'
