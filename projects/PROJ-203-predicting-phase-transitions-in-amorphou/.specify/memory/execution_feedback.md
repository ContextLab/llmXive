# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/descriptor_utils.py: self-declared fabricated metric — “…similar     # For now, return mock values consistent with the task con…”
- code/data/descriptor_utils.py: self-declared fabricated metric — “…descriptors.")         # Use placeholder values if trajectory loading fails…”
- code/data/descriptor_utils.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock trajectory data loading - in production…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/descriptor_utils.py: self-declared fabricated metric — “…similar     # For now, return mock values consistent with the task con…”; code/data/descriptor_utils.py: self-declared fabricated metric — “…descriptors.")         # Use placeholder values if trajectory loading fails…”; code/data/descriptor_utils.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock trajectory data loading - in production…”; 6 command(s) failed: python -m data.run_md_sim --config config.yaml (rc=1); python -m data.extract_descriptors --input data/raw/md_trajectories/ --output data/processed/descriptors.csv (rc=1); python -m data.merge_labels --descriptors data/processed/descriptors.csv --experimental data/raw/literature_subset.csv --output data/processed/final_dataset.csv (rc=1); 4 declared deliverable(s) absent: data/logs/simulation_times.json; data/processed/descriptors.csv; data/processed/final_dataset.parquet

## Failing / missing run-book commands

- python -m data.run_md_sim --config config.yaml -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/data/run_md_sim.py", line 253, in <module>
    sys.exit(main())
    ^^^
NameError: name 'sys' is not defined

- python -m data.extract_descriptors --input data/raw/md_trajectories/ --output data/processed/descriptors.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-203-predicting-phase-transitions-in-amorphou/bin/python: No module named data.extract_descriptors

- python -m data.merge_labels --descriptors data/processed/descriptors.csv --experimental data/raw/literature_subset.csv --output data/processed/final_dataset.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-203-predicting-phase-transitions-in-amorphou/bin/python: No module named data.merge_labels

- python -m models.train_rf --input data/processed/final_dataset.csv --output artifacts/models/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-203-predicting-phase-transitions-in-amorphou/bin/python: No module named models.train_rf

- python -m models.evaluate --model artifacts/models/regressor.pkl --data data/processed/final_dataset.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-203-predicting-phase-transitions-in-amorphou/bin/python: No module named models.evaluate

- python -m models.interpret --model artifacts/models/regressor.pkl --data data/processed/final_dataset.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-203-predicting-phase-transitions-in-amorphou/bin/python: No module named models.interpret


## Declared deliverables still missing

- data/logs/simulation_times.json
- data/processed/descriptors.csv
- data/processed/final_dataset.parquet
- data/raw/pilot_compositions.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/simulation_times.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/run_md_sim.py` — NOT invoked by the run-book
    - `code/data/simulate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/simulation_times.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptor_utils.py` — NOT invoked by the run-book
    - `code/data/merge.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/validators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/finalize_dataset.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils/performance_optimizations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pilot_compositions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/run_md_sim.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/pilot_compositions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
