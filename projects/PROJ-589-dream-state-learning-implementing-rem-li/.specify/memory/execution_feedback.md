# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…model.to(device)      # Dummy data loader – 10 batches of r…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…model.to(device)      # Dummy data loader – 10 batches of r…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/train.py --seed 42 --steps 10 --mode debug; python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20; 2 command(s) failed: python code/data_loader.py --download (rc=1); python code/eval.py --results-dir data/results/ (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/data_loader.py", line 21, in <module>
    from data.loader import verify_dataset_integrity, load_glue_subset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/data/loader.py", line 10, in <module>
    from datasets import load_dataset, DatasetDict
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/datasets/__init__.py", line 24, in <module>
    import pyarrow
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.3

- python code/train.py --seed 42 --steps 10 --mode debug -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py': [Errno 2] No such file or directory

- python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py': [Errno 2] No such file or directory

- python code/eval.py --results-dir data/results/ -> rc=1
:22,807 - __main__ - INFO - Loaded 2 result files
2026-10-18 01:34:22,807 - __main__ - INFO - Running statistical analysis
2026-10-18 01:34:22,807 - __main__ - WARNING - Insufficient results for paired statistical analysis
2026-10-18 01:34:22,808 - __main__ - INFO - Generating evaluation report

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 200, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 184, in main
    report_path = generate_evaluation_report(results, analysis, Path(args.output_dir))
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py", line 135, in generate_evaluation_report
    'interpretation': generate_interpretation(analysis)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: generate_interpretation() missing 3 required positional arguments: 'base_mean', 'diff', and 'p_value'

