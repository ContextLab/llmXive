# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…xdigest()  # --- Step 4: Synthetic Data Generation (T013) ---  d…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Implements T013: Synthetic Data Generation.     Reads da…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…'pending_synthetic',     generates synthetic data based on continuum…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Starting synthetic data generation (T013).")…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…(f"Generating {n_actual} synthetic samples.")      # 5. Generate Da…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic train data to {output_csv}")      #…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("T013 Synthetic Data Generation completed.")…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…ct) -> Dict:     """     Generates a single synthetic data row based on contin…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/02_feature_engineering.py`
- `python code/03_modeling.py`
- `python code/04_analysis.py`
- `python code/run_pipeline.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…xdigest()  # --- Step 4: Synthetic Data Generation (T013) ---  d…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Implements T013: Synthetic Data Generation.     Reads da…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…'pending_synthetic',     generates synthetic data based on continuum…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/02_feature_engineering.py; python code/04_analysis.py; python code/run_pipeline.py; 1 command(s) failed: python code/03_modeling.py (rc=1); 6 declared deliverable(s) absent: data/processed/features.csv; data/processed/targets.csv; data/raw/defect_dataset_2022.csv

## Failing / missing run-book commands

- python code/02_feature_engineering.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/02_feature_engineering.py': [Errno 2] No such file or directory
- python code/03_modeling.py -> rc=1
    2026-08-23 19:22:51,990 - ERROR - Model training failed: Features file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/data/processed/features.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/03_modeling.py", line 378, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/03_modeling.py", line 348, in main
    raise FileNotFoundError(f"Features file not found: {features_path}")
FileNotFoundError: Features file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/data/processed/features.csv
- python code/04_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/04_analysis.py': [Errno 2] No such file or directory
- python code/run_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/run_pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/features.csv
- data/processed/targets.csv
- data/raw/defect_dataset_2022.csv
- data/raw/pristine_structures.csv
- data/raw/real_holdout.csv
- data/validation/Validation_Report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/05_validation.py` — NOT invoked by the run-book
    - `code/03_modeling.py` — IS a run-book command
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/targets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/05_validation.py` — NOT invoked by the run-book
    - `code/03_modeling.py` — IS a run-book command
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/targets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/defect_dataset_2022.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/defect_dataset_2022.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pristine_structures.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
    - `code/generators/synthetic_data_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/pristine_structures.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/real_holdout.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/real_holdout.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/Validation_Report.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_validation.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/Validation_Report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/data/processed/features.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/04_inference.py`, `code/05_validation.py`, `code/03_modeling.py`, `code/02_data_processing.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/data/processed/features.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/04_inference.py`, `code/05_validation.py`, `code/03_modeling.py`, `code/02_data_processing.py`, `code/infrastructure/path_utils.py`.
