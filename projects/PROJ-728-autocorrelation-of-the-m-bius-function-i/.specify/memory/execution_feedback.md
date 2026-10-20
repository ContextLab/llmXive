# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/permutation.py: self-declared fabricated metric — “…lag``) are filled        with placeholder values that satisfy the schema; lat…”
- code/permutation.py: self-declared fabricated metric — “…(null_vals, 97.5))          # Placeholder values for columns that will be fil…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/permutation.py: self-declared fabricated metric — “…lag``) are filled        with placeholder values that satisfy the schema; lat…”; code/permutation.py: self-declared fabricated metric — “…(null_vals, 97.5))          # Placeholder values for columns that will be fil…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json; 4 command(s) failed: python code/main.py (rc=1); python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy (rc=-1); python code/sensitivity.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy --out data/processed/sensitivity_summary.csv (rc=1); 1 declared deliverable(s) absent: data/processed/pipeline_status.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
 start=44622, L=1000, h=1, autocorrelation=-0.047047047047
Window index written to data/processed/window_index.csv (300 rows)
Generated missing window index CSV at data/processed/window_index.csv
Full autocorrelation matrix written to data/processed/autocorrelation_raw.csv

[ERROR] Step 'cross‑validation' failed: Relative error 2.19e-05 exceeds tolerance for window start=44622, L=1000, lag=2
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/main.py", line 211, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/main.py", line 191, in main
    _run_step(cross_validate_main, "cross‑validation")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/main.py", line 64, in _run_step
    step_func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/cross_validate_autocorrelation.py", line 169, in main
    raise RuntimeError(
RuntimeError: Relative error 2.19e-05 exceeds tolerance for window start=44622, L=1000, lag=2

- python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy -> rc=-1


[TIMEOUT after 120s]
- python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-728-autocorrelation-of-the-m-bius-function-i/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/calibration.py': [Errno 2] No such file or directory

- python code/sensitivity.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy --out data/processed/sensitivity_summary.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/sensitivity.py", line 198, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/sensitivity.py", line 97, in main
    raise FileNotFoundError(f"Required stats CSV not found: {STATS_CSV}")
FileNotFoundError: Required stats CSV not found: data/processed/autocorr_stats.csv

- python code/viz.py --stats data/processed/autocorrelation_stats.csv --outdir outputs/figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/viz.py", line 109, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/viz.py", line 100, in main
    raise FileNotFoundError(f"Required CSV not found: {INPUT_CSV}")
FileNotFoundError: Required CSV not found: data/processed/autocorr_stats.csv


## Declared deliverables still missing

- data/processed/pipeline_status.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/pipeline_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/cross_validate_autocorrelation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pipeline_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
