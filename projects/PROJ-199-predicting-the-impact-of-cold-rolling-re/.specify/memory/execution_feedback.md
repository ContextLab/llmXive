# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/robustness.py: synthetic/fake INPUT data not authorized by the spec — “…l import Ridge         # Mock data for demonstration…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…# 3. Fallback to Synthetic             if data is None:…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…"Invoking synthetic dataset generation (T012b)."…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Synthetic dataset generated for {material}…”
- code/data/download_benchmark.py: synthetic/fake INPUT data not authorized by the spec — “…ublic dataset exists, it generates a verified synthetic benchmark based on the p…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic EBSD Dataset Generator for Cold Rolli…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…e Analysis.  This module generates a verified synthetic EBSD dataset for Al, Cu,…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…np.ndarray:     """     Generate synthetic Euler angles for a given…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/robustness.py: synthetic/fake INPUT data not authorized by the spec — “…l import Ridge         # Mock data for demonstration…”; code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…# 3. Fallback to Synthetic             if data is None:…”; code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…"Invoking synthetic dataset generation (T012b)."…”; 6 command(s) failed: python code/__main__.py --task download (rc=1); python code/__main__.py --task preprocess (rc=1); python code/__main__.py --task quantify (rc=1); 6 declared deliverable(s) absent: data/processed/benchmark_data.json; data/processed/cleaned_ebsd.parquet; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/__main__.py --task download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__main__.py", line 5, in <module>
    from code.setup_data_directory import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__init__.py", line 20, in <module>
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
RuntimeError: The 'code/' directory structure is not correctly set up. Please ensure the directory exists relative to this file.

- python code/__main__.py --task preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__main__.py", line 5, in <module>
    from code.setup_data_directory import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__init__.py", line 20, in <module>
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
RuntimeError: The 'code/' directory structure is not correctly set up. Please ensure the directory exists relative to this file.

- python code/__main__.py --task quantify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__main__.py", line 5, in <module>
    from code.setup_data_directory import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__init__.py", line 20, in <module>
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
RuntimeError: The 'code/' directory structure is not correctly set up. Please ensure the directory exists relative to this file.

- python code/__main__.py --task train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__main__.py", line 5, in <module>
    from code.setup_data_directory import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__init__.py", line 20, in <module>
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
RuntimeError: The 'code/' directory structure is not correctly set up. Please ensure the directory exists relative to this file.

- python code/__main__.py --task robustness -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__main__.py", line 5, in <module>
    from code.setup_data_directory import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__init__.py", line 20, in <module>
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
RuntimeError: The 'code/' directory structure is not correctly set up. Please ensure the directory exists relative to this file.

- python code/__main__.py --task full-pipeline -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__main__.py", line 5, in <module>
    from code.setup_data_directory import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/code/__init__.py", line 20, in <module>
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
RuntimeError: The 'code/' directory structure is not correctly set up. Please ensure the directory exists relative to this file.


## Declared deliverables still missing

- data/processed/benchmark_data.json
- data/processed/cleaned_ebsd.parquet
- data/processed/descriptors.csv
- data/processed/mass_balance_report.json
- data/processed/system_mass_balance_summary.json
- data/raw/synthetic_ebsd.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/benchmark_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download_benchmark.py` — NOT invoked by the run-book
    - `code/data/generate_benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/benchmark_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_ebsd.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/consolidate.py` — NOT invoked by the run-book
    - `code/data/consolidate_cleaned.py` — NOT invoked by the run-book
    - `code/data/exclusion.py` — NOT invoked by the run-book
    - `code/features/descriptors.py` — NOT invoked by the run-book
    - `code/features/export_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_ebsd.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/mass_balance_verification.py` — NOT invoked by the run-book
    - `code/analysis/physics_check.py` — NOT invoked by the run-book
    - `code/analysis/robustness.py` — NOT invoked by the run-book
    - `code/analysis/system_mass_balance.py` — NOT invoked by the run-book
    - `code/analysis/texture_validation.py` — NOT invoked by the run-book
    - `code/analysis/trend_validation.py` — NOT invoked by the run-book
    - `code/features/descriptors.py` — NOT invoked by the run-book
    - `code/features/export_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mass_balance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/features/export_final_descriptors.py` — NOT invoked by the run-book
    - `code/features/mass_balance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mass_balance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/system_mass_balance_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/system_mass_balance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/system_mass_balance_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_ebsd.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_synthetic.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_ebsd.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
