# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…rrectly.     3. Create a synthetic dataset with tied fractions to v…”
- code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…: Tie-breaker logic with synthetic data ---     logger.info("Val…”
- code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…g tie-breaker logic with synthetic data...")          # Create a…”
- code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…..")          # Create a synthetic dataset with tied fractions…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…rrectly.     3. Create a synthetic dataset with tied fractions to v…”; code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…: Tie-breaker logic with synthetic data ---     logger.info("Val…”; code/models/train.py: synthetic/fake INPUT data not authorized by the spec — “…g tie-breaker logic with synthetic data...")          # Create a…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 4 command(s) failed: python code/data/download.py (rc=1); python code/models/train.py (rc=1); python code/models/predict.py (rc=1); 3 declared deliverable(s) absent: data/config/ternary_combinations.csv; data/processed/features.csv; data/raw/gfa_dataset.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/main.py': [Errno 2] No such file or directory

- python code/data/download.py -> rc=1
2026-10-10 15:29:53 - __main__ - INFO - Attempting to download dataset (Attempt 1/5)...
2026-10-10 15:29:53 - __main__ - CRITICAL - Critical error during download: Network error during download: 404 Client Error. (Request ID: Root=1-6aca59f1-30df67020c915eab1011b36c;e3b27698-fdc4-48a0-91a4-306034e61bdc)

Entry Not Found for url: https://huggingface.co/datasets/GFA-D2/pilot_flags/resolve/main/pilot_flags.csv.
2026-10-10 15:29:53 - __main__ - CRITICAL - Task failed: Network error during download: 404 Client Error. (Request ID: Root=1-6aca59f1-30df67020c915eab1011b36c;e3b27698-fdc4-48a0-91a4-306034e61bdc)

Entry Not Found for url: https://huggingface.co/datasets/GFA-D2/pilot_flags/resolve/main/pilot_flags.csv.

Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.

- python code/models/train.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/models/train.py", line 396, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/models/train.py", line 380, in main
    config = load_config()
             ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/config/env.py", line 99, in load_config
    logger.log_info(f"Ensured directory exists: {path_obj}")
    ^^^^^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'log_info'

- python code/models/predict.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/models/predict.py", line 321, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/models/predict.py", line 251, in main
    config = load_config()
             ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/code/config/env.py", line 99, in load_config
    logger.log_info(f"Ensured directory exists: {path_obj}")
    ^^^^^^^^^^^^^^^
AttributeError: 'Logger' object has no attribute 'log_info'

- python -m pytest tests/ -> rc=2
ntifying-the-effect-of-alloying-eleme/tests/integration/test_model_training.py:130: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

tests/integration/test_screening.py:141
  /home/runner/work/llmXive/llmXive/projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/tests/integration/test_screening.py:141: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_elements_config.py
ERROR tests/unit/test_environment_config.py
ERROR tests/unit/test_project_structure.py - AttributeError: module 'sys' has...
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 4 warnings, 3 errors in 2.93s =========================



## Declared deliverables still missing

- data/config/ternary_combinations.csv
- data/processed/features.csv
- data/raw/gfa_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/config/ternary_combinations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/predict.py` — IS a run-book command
  Make ONE of these WRITE `data/config/ternary_combinations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/features.py` — IS a run-book command
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/save_features.py` — NOT invoked by the run-book
    - `code/data/validate.py` — NOT invoked by the run-book
    - `code/models/predict.py` — IS a run-book command
    - `code/models/train.py` — IS a run-book command
    - `code/utils/schema_validator.py` — NOT invoked by the run-book
    - `code/utils/shap_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/gfa_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config/environment_defaults.py` — NOT invoked by the run-book
    - `code/data/download.py` — IS a run-book command
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/save_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/gfa_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
