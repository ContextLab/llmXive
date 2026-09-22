# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis.py: self-declared fabricated metric — “…the task, we will calculate a mock value if the library doesn't suppor…”
- code/retrieval.py: metric `water_mixing_ratio` assigned from an RNG draw (line 72)
- code/retrieval.py: synthetic/fake INPUT data not authorized by the spec — “…val()                  # Mock data for demonstration of str…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: self-declared fabricated metric — “…the task, we will calculate a mock value if the library doesn't suppor…”; code/retrieval.py: metric `water_mixing_ratio` assigned from an RNG draw (line 72); code/retrieval.py: synthetic/fake INPUT data not authorized by the spec — “…val()                  # Mock data for demonstration of str…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 command(s) failed: python code/download.py --output data/raw (rc=1); python code/retrieval.py --input data/raw --output data/processed (rc=1); python code/analysis.py --input data/processed/analysis_dataset.csv --output results (rc=1); 7 declared deliverable(s) absent: data/processed/analysis_results.json; data/processed/bootstrap_ci.json; data/processed/correlation_stats.json

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/main.py': [Errno 2] No such file or directory
- python code/download.py --output data/raw -> rc=1
    2026-09-22 19:34:27,307 - llmXive - INFO - Starting T013a: Count unique planets
2026-09-22 19:34:27,307 - llmXive - ERROR - T013a failed: 'dict' object has no attribute 'data_dir'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 84, in main
    count = count_unique_planets()
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 33, in count_unique_planets
    metadata_path = str(config.data_dir / "processed" / "metadata.csv")
                        ^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'data_dir'
- python code/retrieval.py --input data/raw --output data/processed -> rc=1
    Retrieval process failed: Input directory not found: data/raw
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 255, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 248, in main
    results = process_retrieval_results(args.input, args.output)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 180, in process_retrieval_results
    spectrum_files = load_spectrum_files(input_dir)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 112, in load_spectrum_files
    raise FileNotFoundError(f"Input directory not found: {input_dir}")
FileNotFoundError: Input directory not found: data/raw
- python code/analysis.py --input data/processed/analysis_dataset.csv --output results -> rc=1
    WARNING:root:scikit-survival not available. Censored correlation features will be limited.
ERROR:root:Failed to load data: Analysis dataset not found at data/processed/analysis_dataset.csv

## Declared deliverables still missing

- data/processed/analysis_results.json
- data/processed/bootstrap_ci.json
- data/processed/correlation_stats.json
- data/processed/count_report.json
- data/processed/metadata.csv
- data/processed/regression_results.json
- data/processed/retrieval_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/noise_stability.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/instrument_calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bootstrap_ci.json` is declared but was NOT written. Scripts referencing it:
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/correlation_stats.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/bootstrap_ci.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/correlation_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/count_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/count_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/noise_stability.py` — NOT invoked by the run-book
    - `code/retrieval.py` — IS a run-book command
    - `code/spectral_resolution_report.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/detection_limit_analysis.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/regression_stats.py` — NOT invoked by the run-book
    - `code/analysis_tobit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/retrieval_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/retrieval.py` — IS a run-book command
    - `code/mdc_stats.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/detection_limit_analysis.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/retrieval_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
