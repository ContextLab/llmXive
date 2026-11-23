# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analyzer.py: self-declared fabricated metric — “…size=0.0).")         # Return dummy result         return pd.DataFrame()…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analyzer.py: self-declared fabricated metric — “…size=0.0).")         # Return dummy result         return pd.DataFrame()…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/simulation_runner.py --config code/config.yaml; python code/analyzers.py --input data/processed/error_rates.csv --output data/analysis/; 2 command(s) failed: python code/run_data_gen.py --config code/config.yaml (rc=1); python -m pytest tests/unit/ (rc=1); 4 declared deliverable(s) absent: data/processed/error_rates.csv; data/processed/raw_pvalues.csv; data/processed/stability_trend.csv

## Failing / missing run-book commands

- python code/run_data_gen.py --config code/config.yaml -> rc=1
enerating scenario: n=10, dist=normal, effect=0.0
2026-10-10 16:18:21,224 - __main__ - ERROR -   -> Failed for scenario {'n': 10, 'dist': 'normal', 'effect': 0.0}: Missing required argument: 'effect_size' or 'eff'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 145, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 142, in main
    generate_validation_dataset(output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/run_data_gen.py", line 88, in generate_validation_dataset
    data_dict = generate_data(n, dist_type, effect_size, seed=scenario_seed)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/data_generator.py", line 131, in generate_data
    raise ValueError("Missing required argument: 'effect_size' or 'eff'")
ValueError: Missing required argument: 'effect_size' or 'eff'

- python code/simulation_runner.py --config code/config.yaml -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/simulation_runner.py': [Errno 2] No such file or directory

- python code/analyzers.py --input data/processed/error_rates.csv --output data/analysis/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/analyzers.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/error_rates.csv
- data/processed/raw_pvalues.csv
- data/processed/stability_trend.csv
- data/raw/sample_validation.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/error_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/export_results.py` — NOT invoked by the run-book
    - `code/run_analyzer.py` — NOT invoked by the run-book
    - `code/run_simulation.py` — NOT invoked by the run-book
    - `code/simulation_engine.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/visualizer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/error_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/export_results.py` — NOT invoked by the run-book
    - `code/run_analyzer.py` — NOT invoked by the run-book
    - `code/run_log_pvalue_analysis.py` — NOT invoked by the run-book
    - `code/run_optimized_simulation.py` — NOT invoked by the run-book
    - `code/run_simulation.py` — NOT invoked by the run-book
    - `code/simulation_engine.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stability_trend.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/run_simulation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stability_trend.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sample_validation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_data_gen.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/sample_validation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
