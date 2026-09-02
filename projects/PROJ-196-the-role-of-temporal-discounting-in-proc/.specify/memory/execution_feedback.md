# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ndom_state):     """     Generate synthetic delay discounting data.…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ndom_state):     """     Generate synthetic procrastination scale da…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ndom_state):     """     Generate synthetic n-back working memory ta…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…print("CRITICAL: Synthetic data reliability below thresh…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ndom_state):     """     Generate synthetic delay discounting data.…”; code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ndom_state):     """     Generate synthetic procrastination scale da…”; code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ndom_state):     """     Generate synthetic n-back working memory ta…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python code/ingestion.py --mode generate --n [N] --seed 42, where N represents a sufficiently large sample size to ensure statistical power for the study. (rc=1); 4 declared deliverable(s) absent: data/processed/final_analysis_report.json; data/processed/harmonized_dataset.parquet; data/processed/model_config.json

## Failing / missing run-book commands

- python code/ingestion.py --mode generate --n [N] --seed 42, where N represents a sufficiently large sample size to ensure statistical power for the study. -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/ingestion.py", line 444, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/ingestion.py", line 380, in main
    config = get_config()
             ^^^^^^^^^^
NameError: name 'get_config' is not defined
- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/final_analysis_report.json
- data/processed/harmonized_dataset.parquet
- data/processed/model_config.json
- data/processed/regression_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/harmonized_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/harmonized_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
