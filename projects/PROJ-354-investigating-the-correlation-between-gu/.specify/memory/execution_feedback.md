# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…is module implements: 1. Synthetic dataset generation with a known…”
- code/power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset for power analys…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…is module implements: 1. Synthetic dataset generation with a known…”; code/power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset for power analys…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/pipelines/analyze.py  --input data/processed/ilr_transformed.parquet  --output results/associations/; python code/paper/plots.py  --input results/associations/main_effects.parquet  --output results/plots/; 3 command(s) failed: python code/download.py --seed 42 --output data/raw/ukb_microbiome.parquet --cognitive-output data/raw/ukb_cognitive.parquet (rc=1); python code/preprocess.py --input data/raw/ukb_microbiome.parquet data/raw/ukb_cognitive.parquet --fallback data/raw/synthetic_ukb.parquet --output data/processed/ilr_transformed.parquet (rc=1); python -m pytest tests/ -v (rc=2); 2 declared deliverable(s) absent: data/processed/filtered_cohort.parquet; data/processed/zero_replaced_counts.parquet

## Failing / missing run-book commands

- python code/download.py --seed 42 --output data/raw/ukb_microbiome.parquet --cognitive-output data/raw/ukb_cognitive.parquet -> rc=1
INFO     | llmXive.root | Logging infrastructure initialized.
INFO     | llmXive.root | Log directory: /home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/logs
INFO     | llmXive.root | Python version: 3.11.17 (main, Oct  1 2026, 14:32:31) [GCC 13.3.0]
WARNING  | __main__ | HuggingFace datasets library not installed. Install with: pip install datasets
INFO     | __main__ | Starting data download process...
CRITICAL | __main__ | Unexpected error in download script: "Path key 'data/processed' not found in PATHS"


- python code/preprocess.py --input data/raw/ukb_microbiome.parquet data/raw/ukb_cognitive.parquet --fallback data/raw/synthetic_ukb.parquet --output data/processed/ilr_transformed.parquet -> rc=1
ng-the-correlation-between-gu/code/preprocess.py", line 299, in main
    result = run_preprocessing_pipeline()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/preprocess.py", line 292, in run_preprocessing_pipeline
    return run_ilr_pipeline()
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/preprocess.py", line 249, in run_ilr_pipeline
    df_micro = load_raw_microbiome_data()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/preprocess.py", line 27, in load_raw_microbiome_data
    input_path = get_path("data/processed/zero_replaced_counts.parquet")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/config.py", line 99, in get_path
    raise KeyError(f"Path key '{key}' not found in PATHS")
KeyError: "Path key 'data/processed/zero_replaced_counts.parquet' not found in PATHS"

- python code/pipelines/analyze.py  --input data/processed/ilr_transformed.parquet  --output results/associations/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/pipelines/analyze.py': [Errno 2] No such file or directory

- python code/paper/plots.py  --input results/associations/main_effects.parquet  --output results/plots/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-354-investigating-the-correlation-between-gu/code/paper/plots.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
mport_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    exec(co, module.__dict__)
tests/test_preprocess_integration.py:21: in <module>
    from code.preprocessing import (
E   ModuleNotFoundError: No module named 'code.preprocessing'
=========================== short test summary info ============================
ERROR tests/test_analysis_citations.py
ERROR tests/test_config_env.py
ERROR tests/test_config_manager.py
ERROR tests/test_preprocess.py
ERROR tests/test_preprocess_integration.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 skipped, 5 errors in 2.02s =========================



## Declared deliverables still missing

- data/processed/filtered_cohort.parquet
- data/processed/zero_replaced_counts.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_cohort.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/generate_retention_log.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_cohort.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/zero_replaced_counts.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/generate_retention_log.py` — NOT invoked by the run-book
    - `code/models/microbiome.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/zero_replace.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/zero_replaced_counts.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
