# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_golden_set_template.py: self-declared fabricated metric — “…hetic Data**: Do not generate fake scores. Your expert judgment is req…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_golden_set_template.py: self-declared fabricated metric — “…hetic Data**: Do not generate fake scores. Your expert judgment is req…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; 1 command(s) failed: python code/load_data.py --download (rc=1); 6 declared deliverable(s) absent: data/explanation_tiers/complex_tiers.csv; data/explanation_tiers/moderate_tiers.csv; data/explanation_tiers/simple_tiers.csv

## Failing / missing run-book commands

- python code/load_data.py --download -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-553-cognitive-load-optimization-adaptive-com/code/load_data.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/run_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-553-cognitive-load-optimization-adaptive-com/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-553-cognitive-load-optimization-adaptive-com/code/run_pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/explanation_tiers/complex_tiers.csv
- data/explanation_tiers/moderate_tiers.csv
- data/explanation_tiers/simple_tiers.csv
- data/processed/golden_set.csv
- data/processed/instructional_units.csv
- data/simulation_results/hysteresis_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/explanation_tiers/complex_tiers.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_and_tune_tiers.py` — NOT invoked by the run-book
    - `code/generate_complex_tier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/explanation_tiers/complex_tiers.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/explanation_tiers/moderate_tiers.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_and_tune_tiers.py` — NOT invoked by the run-book
    - `code/generate_simple_tier.py` — NOT invoked by the run-book
    - `code/generate_moderate_tier.py` — NOT invoked by the run-book
    - `code/generate_complex_tier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/explanation_tiers/moderate_tiers.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/explanation_tiers/simple_tiers.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_and_tune_tiers.py` — NOT invoked by the run-book
    - `code/generate_simple_tier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/explanation_tiers/simple_tiers.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/golden_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_golden_set.py` — NOT invoked by the run-book
    - `code/validate_and_load_golden_set.py` — NOT invoked by the run-book
    - `code/acquire_golden_set.py` — NOT invoked by the run-book
    - `code/utils.py` — NOT invoked by the run-book
    - `code/load_data.py` — IS a run-book command
    - `code/create_golden_set.py` — NOT invoked by the run-book
    - `code/train_load_model.py` — NOT invoked by the run-book
    - `code/generate_golden_set_template.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/golden_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/instructional_units.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extract_instructional_units.py` — NOT invoked by the run-book
    - `code/generate_tiers.py` — NOT invoked by the run-book
    - `code/utils.py` — NOT invoked by the run-book
    - `code/generate_moderate_tier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/instructional_units.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation_results/hysteresis_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/hysteresis_controller.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation_results/hysteresis_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
