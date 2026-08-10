# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…turn True  # --- Step 4: Synthetic Data Generation (T013) ---  d…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…List[Dict]:     """     Generates synthetic data rows based on conti…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Starting synthetic data generation. Target: {n_t…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Implements T013: Synthetic Data Generation.     Reads da…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Starting synthetic data generation (T013).")…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…ic_data)          # Save synthetic train data     output_csv = project…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic train data to {output_csv}")…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("T013 Synthetic Data Generation completed suc…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…turn True  # --- Step 4: Synthetic Data Generation (T013) ---  d…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…List[Dict]:     """     Generates synthetic data rows based on conti…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Starting synthetic data generation. Target: {n_t…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/run_workflow.py; 7 declared deliverable(s) absent: data/processed/features.csv; data/processed/targets.csv; data/raw/defect_dataset_2022.csv

## Failing / missing run-book commands

- python code/run_workflow.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-209-quantifying-the-influence-of-topological/code/run_workflow.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/features.csv
- data/processed/targets.csv
- data/raw/defect_dataset_2022.csv
- data/raw/pristine_structures.csv
- data/raw/real_holdout.csv
- data/state/mock_dftb_exclusions.json
- data/validation/Validation_Report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_validation.py` — NOT invoked by the run-book
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/03_modeling.py` — NOT invoked by the run-book
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/targets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_validation.py` — NOT invoked by the run-book
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/03_modeling.py` — NOT invoked by the run-book
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/targets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/defect_dataset_2022.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/04_inference.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/defect_dataset_2022.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pristine_structures.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_acquisition.py` — NOT invoked by the run-book
    - `code/02_data_processing.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
    - `code/generators/synthetic_data_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/pristine_structures.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/real_holdout.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/real_holdout.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/state/mock_dftb_exclusions.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/state/mock_dftb_exclusions.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/Validation_Report.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_validation.py` — NOT invoked by the run-book
    - `code/infrastructure/path_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/Validation_Report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
