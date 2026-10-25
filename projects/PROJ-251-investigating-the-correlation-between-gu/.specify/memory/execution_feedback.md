# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_fetch_strategy_a.py: synthetic/fake INPUT data not authorized by the spec — “…peline will fall back to synthetic data generation (T011b) as pe…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic OTU table with controlle…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic serology metadata with c…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…Main entry point to generate synthetic dataset.     Reads confi…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Starting synthetic data generation task T011b")…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…1b")          # Check if synthetic data is enabled     if not ge…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…_DATA is False. Skipping synthetic data generation.")         re…”
- code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic data: N={n_subjects}, Taxa={n…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 18 fabricated/simulated-result signal(s) — results are not real measurements: code/01_fetch_strategy_a.py: synthetic/fake INPUT data not authorized by the spec — “…peline will fall back to synthetic data generation (T011b) as pe…”; code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic OTU table with controlle…”; code/01_generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic serology metadata with c…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main_pipeline.py; 1 command(s) failed: python -m pytest tests/ -v (rc=2); 8 declared deliverable(s) absent: data/processed/cleared.csv; data/processed/cleared_final.csv; data/processed/cleared_log.csv

## Failing / missing run-book commands

- python code/main_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-251-investigating-the-correlation-between-gu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-251-investigating-the-correlation-between-gu/code/main_pipeline.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
uleNotFoundError: No module named 'dotenv'
________________ ERROR collecting tests/test_validate_schema.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-251-investigating-the-correlation-between-gu/tests/test_validate_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_validate_schema.py:17: in <module>
    from code.utils.config import get_specs_path
code/utils/config.py:3: in <module>
    from dotenv import load_dotenv
E   ModuleNotFoundError: No module named 'dotenv'
=========================== short test summary info ============================
ERROR tests/test_clr_transformation.py
ERROR tests/test_env_manager.py
ERROR tests/test_linting_setup.py
ERROR tests/test_sra_downloader.py
ERROR tests/test_sra_fetcher.py
ERROR tests/test_validate_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 0.43s ===============================



## Declared deliverables still missing

- data/processed/cleared.csv
- data/processed/cleared_final.csv
- data/processed/cleared_log.csv
- data/processed/cleared_shannon.csv
- data/raw/otutable.csv
- data/raw/serology.csv
- data/results/model_metrics.json
- data/results/sc004_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleared.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_merge_strategy_b.py` — NOT invoked by the run-book
    - `code/01_validate_schema.py` — NOT invoked by the run-book
    - `code/020_apply_clr.py` — NOT invoked by the run-book
    - `code/020_calculate_shannon.py` — NOT invoked by the run-book
    - `code/020_normalize_abundance.py` — NOT invoked by the run-book
    - `code/02_apply_log_titers.py` — NOT invoked by the run-book
    - `code/02_preprocess.py` — NOT invoked by the run-book
    - `code/03_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleared.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleared_final.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_validate_schema.py` — NOT invoked by the run-book
    - `code/020_apply_clr.py` — NOT invoked by the run-book
    - `code/03_correlation.py` — NOT invoked by the run-book
    - `code/03_variance_filter.py` — NOT invoked by the run-book
    - `code/04_modeling.py` — NOT invoked by the run-book
    - `code/05_nested_cv_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleared_final.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleared_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/020_apply_clr.py` — NOT invoked by the run-book
    - `code/02_apply_log_titers.py` — NOT invoked by the run-book
    - `code/05_nested_cv_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleared_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleared_shannon.csv` is declared but was NOT written. Scripts referencing it:
    - `code/020_apply_clr.py` — NOT invoked by the run-book
    - `code/020_calculate_shannon.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleared_shannon.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/otutable.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_fetch_strategy_a.py` — NOT invoked by the run-book
    - `code/01_generate_synthetic.py` — NOT invoked by the run-book
    - `code/01_merge_strategy_b.py` — NOT invoked by the run-book
    - `code/download.py` — NOT invoked by the run-book
    - `code/utils/sra_fetcher.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/otutable.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/serology.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_fetch_strategy_a.py` — NOT invoked by the run-book
    - `code/01_generate_synthetic.py` — NOT invoked by the run-book
    - `code/01_merge_strategy_b.py` — NOT invoked by the run-book
    - `code/01_sra_search.py` — NOT invoked by the run-book
    - `code/download.py` — NOT invoked by the run-book
    - `code/tests/test_sra_fetcher.py` — NOT invoked by the run-book
    - `code/utils/data_loader.py` — NOT invoked by the run-book
    - `code/utils/sra_downloader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/serology.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/036_calculate_metrics.py` — NOT invoked by the run-book
    - `code/036b_success_criterion_check.py` — NOT invoked by the run-book
    - `code/037_write_model_metrics.py` — NOT invoked by the run-book
    - `code/038_validate_model_metrics.py` — NOT invoked by the run-book
    - `code/05_nested_cv_sensitivity.py` — NOT invoked by the run-book
    - `code/utils/validators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sc004_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/025_measure_sc004.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sc004_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
