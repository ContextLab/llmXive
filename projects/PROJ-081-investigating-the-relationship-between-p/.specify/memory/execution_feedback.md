# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/preprocess.py: self-declared fabricated metric — “…s missing or contains NaNs, a placeholder value ``"unknown"`` is inserted so…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/preprocess.py: self-declared fabricated metric — “…s missing or contains NaNs, a placeholder value ``"unknown"`` is inserted so…”; 4 command(s) failed: python code/src/run_pipeline.py --seed 42 --max-species 100 --output-dir outputs/ (rc=1); python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml (rc=1); python -m llmxive_toolkit.validate_contracts  --data "$result_file"  --schema contracts/model_output.schema.yaml (rc=1); 1 declared deliverable(s) absent: data/processed/clean.parquet

## Failing / missing run-book commands

- python code/src/run_pipeline.py --seed 42 --max-species 100 --output-dir outputs/ -> rc=1
Fetching MetaboLights data...
Fetching PMN data...
Fetching HPID data...

2026-10-22 21:26:51,508 INFO code.src.fetch_data: MetaboLights fetch succeeded – 150 records
2026-10-22 21:26:51,787 INFO code.src.fetch_data: PMN fetch succeeded – 342 records
2026-10-22 21:26:51,825 INFO code.src.fetch_data: HPID fetch succeeded – 714 records
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 111, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 87, in main
    pd.concat(raw_dataframes, ignore_index=True, sort=False)
    ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python -m llmxive_toolkit.validate_contracts  --data outputs/clean.parquet  --schema contracts/processed_data.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python -m llmxive_toolkit.validate_contracts  --data "$result_file"  --schema contracts/model_output.schema.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-081-investigating-the-relationship-between-p/bin/python: No module named llmxive_toolkit.validate_contracts

- python code/src/run_pipeline.py --seed 42 --use-placeholder --output-dir outputs_demo/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 111, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-081-investigating-the-relationship-between-p/code/src/run_pipeline.py", line 66, in main
    raise RuntimeError(
RuntimeError: Placeholder data is not permitted for T002. The pipeline requires real datasets from MetaboLights, PMN, and HPID.


## Declared deliverables still missing

- data/processed/clean.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clean.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/correlation_analysis.py` — NOT invoked by the run-book
    - `code/src/preprocess.py` — NOT invoked by the run-book
    - `code/src/run_pipeline.py` — IS a run-book command
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clean.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
