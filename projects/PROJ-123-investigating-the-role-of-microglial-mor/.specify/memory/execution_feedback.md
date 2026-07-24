# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/synthetic_data.py: metric `cognitive_score` assigned from an RNG draw (line 84)
- code/synthetic_data.py: metric `cognitive_score` assigned from an RNG draw (line 86)
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…eck is skipped (assuming synthetic data or external join later).…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…rts modes for generating synthetic data (for validation) and run…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…help='Output path for synthetic data (mode: generate-syntheti…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…# Generate synthetic data             run_syn…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Synthetic data generated at {output_pat…”
- code/run_t018_output.py: synthetic/fake INPUT data not authorized by the spec — “…013-T017 output) and the synthetic data path for validation purp…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv`
- `python code/main.py --mode run-full --data data/processed/synthetic_dataset.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 24 fabricated/simulated-result signal(s) — results are not real measurements: code/synthetic_data.py: metric `cognitive_score` assigned from an RNG draw (line 84); code/synthetic_data.py: metric `cognitive_score` assigned from an RNG draw (line 86); code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…eck is skipped (assuming synthetic data or external join later).…”; 2 command(s) failed: python code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv (rc=1); python code/main.py --mode run-full --data data/processed/synthetic_dataset.csv (rc=1); 1 declared deliverable(s) absent: data/processed/morphological_metrics.csv

## Failing / missing run-book commands

- python code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv -> rc=1
    2026-07-24 06:36:58,502 - __main__ - INFO - Mode: generate-synthetic
2026-07-24 06:36:58,503 - __main__ - ERROR - Pipeline failed: run_synthetic_pipeline() got an unexpected keyword argument 'output_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-123-investigating-the-role-of-microglial-mor/code/main.py", line 59, in main
    run_synthetic_pipeline(output_path=output_path)
TypeError: run_synthetic_pipeline() got an unexpected keyword argument 'output_path'
- python code/main.py --mode run-full --data data/processed/synthetic_dataset.csv -> rc=1
    2026-07-24 06:36:59,829 - __main__ - INFO - Mode: run-full
2026-07-24 06:36:59,829 - __main__ - INFO - Using provided data: data/processed/synthetic_dataset.csv
2026-07-24 06:36:59,829 - __main__ - INFO - Running analysis pipeline...
2026-07-24 06:36:59,829 - __main__ - ERROR - Pipeline failed: run_analysis_pipeline() got an unexpected keyword argument 'input_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-123-investigating-the-role-of-microglial-mor/code/main.py", line 79, in main
    analysis_results = run_analysis_pipeline(input_path=str(metrics_path))
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: run_analysis_pipeline() got an unexpected keyword argument 'input_path'

## Declared deliverables still missing

- data/processed/morphological_metrics.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_analysis_pipeline` — defined in `code/analysis.py`; called 2 way(s):

- code/main.py: analysis_results = run_analysis_pipeline(input_path=str(metrics_path))
- code/analysis.py: result = run_analysis_pipeline(df)

Make `run_analysis_pipeline` in `code/analysis.py` accept ALL of the above.

### `run_synthetic_pipeline` — defined in `code/synthetic_data.py`; called 3 way(s):

- code/main.py: run_synthetic_pipeline(output_path=output_path)
- code/synthetic_data.py: path = run_synthetic_pipeline()
- code/run_t018_output.py: synthetic_path = run_synthetic_pipeline()

Make `run_synthetic_pipeline` in `code/synthetic_data.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/morphological_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/output_metrics.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/morphological_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
