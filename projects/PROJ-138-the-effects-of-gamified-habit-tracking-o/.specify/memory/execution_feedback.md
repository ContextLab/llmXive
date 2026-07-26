# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/fdr_correction.py: self-declared fabricated metric — “…# If not, we construct a mock results set based on the task requir…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…real data or generating synthetic data if real data is missing.…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…data from real source or generate synthetic data.          Returns:…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…L_DATA_PATH}. Generating synthetic data...")         # Generate…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…etic data...")         # Generate synthetic data with seed=42 as per…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…fo(f"Generated {len(df)} synthetic records")          # Step 3: Val…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the habit…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic dataset.          Args:…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 22 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/fdr_correction.py: self-declared fabricated metric — “…# If not, we construct a mock results set based on the task requir…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…real data or generating synthetic data if real data is missing.…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…data from real source or generate synthetic data.          Returns:…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python code/data/synthetic_generator.py --seed [RANDOM_SEED] --n_users --weeks 50 (rc=1); 4 declared deliverable(s) absent: data/processed/merged_data.csv; data/processed/psychometrics.json; data/raw/habitica_data.csv

## Failing / missing run-book commands

- python code/data/synthetic_generator.py --seed [RANDOM_SEED] --n_users --weeks 50 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-138-the-effects-of-gamified-habit-tracking-o/code/data/synthetic_generator.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-138-the-effects-of-gamified-habit-tracking-o/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-138-the-effects-of-gamified-habit-tracking-o/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/merged_data.csv
- data/processed/psychometrics.json
- data/raw/habitica_data.csv
- data/raw/synthetic_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/versioning_runner.py` — NOT invoked by the run-book
    - `code/utils/versioning.py` — NOT invoked by the run-book
    - `code/analysis/robustness.py` — NOT invoked by the run-book
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
    - `code/analysis/modeling.py` — NOT invoked by the run-book
    - `code/analysis/survival.py` — NOT invoked by the run-book
    - `code/tests/test_report.py` — NOT invoked by the run-book
    - `code/reports/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/psychometrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/reports/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/psychometrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/habitica_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/habitica_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/versioning.py` — NOT invoked by the run-book
    - `code/data/merge.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/synthetic_generator.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/synthetic_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
