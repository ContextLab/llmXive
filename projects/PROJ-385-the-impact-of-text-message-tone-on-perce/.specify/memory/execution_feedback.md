# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_verify_consent.py: self-declared fabricated metric — “…ate provenance.json file with placeholder values."""     template = {…”
- code/stubs/mock_prolific_api.py: self-declared fabricated metric — “…be empty")          # Return mock results structure         return {…”
- code/00_generate_synthetic_power_data.py: synthetic/fake INPUT data not authorized by the spec — “…ysis Dataset Generator.  Generates synthetic datasets for power analy…”
- code/00_generate_synthetic_power_data.py: synthetic/fake INPUT data not authorized by the spec — “…containing CSVs with the synthetic data. """ import argparse imp…”
- code/00_generate_synthetic_power_data.py: synthetic/fake INPUT data not authorized by the spec — “…s: dict) -> list:     """Generate the full synthetic dataset."""     setup_si…”
- code/00_generate_synthetic_power_data.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic power analysis datasets.…”
- code/00_generate_synthetic_power_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with N={args.n_participa…”
- code/00_run_power_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…list:     """     Loads synthetic datasets from the provided zip fi…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 22 fabricated/simulated-result signal(s) — results are not real measurements: code/00_verify_consent.py: self-declared fabricated metric — “…ate provenance.json file with placeholder values."""     template = {…”; code/stubs/mock_prolific_api.py: self-declared fabricated metric — “…be empty")          # Return mock results structure         return {…”; code/00_generate_synthetic_power_data.py: synthetic/fake INPUT data not authorized by the spec — “…ysis Dataset Generator.  Generates synthetic datasets for power analy…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/02_collect_real_data.py --mode verify; python code/benchmark_runtime.py; 4 command(s) failed: python code/01_generate_stimuli.py # produces data/raw/stimuli.csv (rc=1); python code/run_pipeline.py (rc=1); python utils/validate_manifest.py (rc=1); 10 declared deliverable(s) absent: data/consent/provenance.json; data/manifest.json; data/processed/analysis_ready.csv

## Failing / missing run-book commands

- python code/01_generate_stimuli.py # produces data/raw/stimuli.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-385-the-impact-of-text-message-tone-on-perce/code/01_generate_stimuli.py", line 25, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

- python code/02_collect_real_data.py --mode verify -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-385-the-impact-of-text-message-tone-on-perce/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-385-the-impact-of-text-message-tone-on-perce/code/02_collect_real_data.py': [Errno 2] No such file or directory

- python code/run_pipeline.py -> rc=1
2026-10-12 18:34:17,720 - llmXive - INFO - Logging infrastructure initialized. Pipeline log started.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-385-the-impact-of-text-message-tone-on-perce/code/run_pipeline.py", line 27, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

- python utils/validate_manifest.py -> rc=1

ERROR: Usage: python validate_manifest.py <path_to_manifest.json>

- python -m pytest -q tests/contract/ -> rc=2

==================================== ERRORS ====================================
________________ ERROR collecting tests/contract/test_config.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-385-the-impact-of-text-message-tone-on-perce/tests/contract/test_config.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_config.py:12: in <module>
    from config import (
E   ImportError: cannot import name 'BASE_DATA_PATH_STR' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-385-the-impact-of-text-message-tone-on-perce/code/config.py)
=========================== short test summary info ============================
ERROR tests/contract/test_config.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.37s


- python code/benchmark_runtime.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-385-the-impact-of-text-message-tone-on-perce/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-385-the-impact-of-text-message-tone-on-perce/code/benchmark_runtime.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/consent/provenance.json
- data/manifest.json
- data/processed/analysis_ready.csv
- data/processed/anonymised_ratings.csv
- data/processed/counterbalanced_trials.csv
- data/processed/power_analysis_results.json
- data/processed/presentation_orders.csv
- data/raw/real_ratings.csv
- data/raw/stimuli.csv
- data/results/posthoc_tukey.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/consent/provenance.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_verify_consent.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/consent/provenance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/99_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_ready.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_fit_lmm.py` — NOT invoked by the run-book
    - `code/04_fit_lmm_satterthwaite.py` — NOT invoked by the run-book
    - `code/06_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_ready.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/anonymised_ratings.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_clean_data.py` — NOT invoked by the run-book
    - `code/052_compute_checksum_anonymised.py` — NOT invoked by the run-book
    - `code/05_anonymise_ratings.py` — NOT invoked by the run-book
    - `code/086_validate_participant_entity.py` — NOT invoked by the run-book
    - `code/99_manifest.py` — NOT invoked by the run-book
    - `code/99_preanalysis_guard.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/anonymised_ratings.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/counterbalanced_trials.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_counterbalance.py` — NOT invoked by the run-book
    - `code/03_random_order.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/counterbalanced_trials.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_power_analysis.py` — NOT invoked by the run-book
    - `code/00_run_power_simulation.py` — NOT invoked by the run-book
    - `code/02_simulate_ratings.py` — NOT invoked by the run-book
    - `code/04_collect_real_data.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/09_power_curve_plotter.py` — NOT invoked by the run-book
    - `code/run_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/power_analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/presentation_orders.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_random_order.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/presentation_orders.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/real_ratings.csv` is declared but was NOT written. Scripts referencing it:
    - `code/041_verify_real_ratings.py` — NOT invoked by the run-book
    - `code/04_collect_real_data.py` — NOT invoked by the run-book
    - `code/05_anonymise_ratings.py` — NOT invoked by the run-book
    - `code/05_compute_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/real_ratings.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/stimuli.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_generate_synthetic_power_data.py` — NOT invoked by the run-book
    - `code/00_power_analysis.py` — NOT invoked by the run-book
    - `code/01_generate_stimuli.py` — IS a run-book command
    - `code/02_counterbalance.py` — NOT invoked by the run-book
    - `code/02_simulate_ratings.py` — NOT invoked by the run-book
    - `code/03_clean_data.py` — NOT invoked by the run-book
    - `code/04_collect_real_data.py` — NOT invoked by the run-book
    - `code/04_run_lmm.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/stimuli.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/posthoc_tukey.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_posthoc.py` — NOT invoked by the run-book
    - `code/07_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/posthoc_tukey.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
