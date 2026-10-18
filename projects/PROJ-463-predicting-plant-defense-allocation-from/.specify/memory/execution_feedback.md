# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/analysis/de_analysis.py: self-declared fabricated metric — “…output         # Here we use dummy values for species/tissue/treatment…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…ta/ │ ├── raw/ # Raw and synthetic data files │ ├── processed/ #…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…adata │ └── synthetic/ # Synthetic validation data ├── requirements.txt # P…”
- code/quickstart.md: synthetic/fake INPUT data not authorized by the spec — “…(Validation)  This mode generates synthetic data to validate the pip…”
- code/quickstart.md: synthetic/fake INPUT data not authorized by the spec — “…l biological data.  1. **Generate Synthetic Data**:  ```bash  python…”
- code/scripts/run_synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Script runner for synthetic data generation. """ import s…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Structural…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…Structural Validation.  Generates structurally valid synthetic TPM count matrices and m…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 43 fabricated/simulated-result signal(s) — results are not real measurements: src/analysis/de_analysis.py: self-declared fabricated metric — “…output         # Here we use dummy values for species/tissue/treatment…”; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…ta/ │ ├── raw/ # Raw and synthetic data files │ ├── processed/ #…”; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…adata │ └── synthetic/ # Synthetic validation data ├── requirements.txt # P…”; 3 command(s) failed: python -m src.cli.run_pipeline --mode real --min-studies [threshold] --min-replicates 2 (rc=1); python -m src.cli.run_pipeline --mode synthetic (rc=1); python -m pytest tests/contract/test_schemas.py (rc=2); 5 declared deliverable(s) absent: data/manifests/batch_correction_report.json; data/manifests/reproducibility_report.json; data/processed/aggregated_features.csv

## Failing / missing run-book commands

- python -m src.cli.run_pipeline --mode real --min-studies [threshold] --min-replicates 2 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-463-predicting-plant-defense-allocation-from/bin/python: No module named src.cli.run_pipeline

- python -m src.cli.run_pipeline --mode synthetic -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-463-predicting-plant-defense-allocation-from/bin/python: No module named src.cli.run_pipeline

- python -m pytest tests/contract/test_schemas.py -> rc=2
achedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-463-predicting-plant-defense-allocation-from/code
configfile: pyproject.toml
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
_________________ ERROR collecting tests/unit/test_schemas.py __________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-463-predicting-plant-defense-allocation-from/code/tests/unit/test_schemas.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/unit/test_schemas.py:11: in <module>
    from src.utils.schemas import (
E   ModuleNotFoundError: No module named 'src.utils.schemas'
=========================== short test summary info ============================
ERROR code/tests/unit/test_schemas.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.12s ===============================



## Declared deliverables still missing

- data/manifests/batch_correction_report.json
- data/manifests/reproducibility_report.json
- data/processed/aggregated_features.csv
- data/processed/final_aggregated_traits.json
- data/processed/post_qc_species_list.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/manifests/batch_correction_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/batch_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifests/batch_correction_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/manifests/reproducibility_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/reproducibility.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifests/reproducibility_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aggregated_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/reproducibility.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aggregated_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_aggregated_traits.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/traits.py` — NOT invoked by the run-book
    - `code/src/data/traits_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_aggregated_traits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/post_qc_species_list.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/phylogeny_fetcher.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/data/traits_fallback.py` — NOT invoked by the run-book
    - `code/src/data/traits_gate.py` — NOT invoked by the run-book
    - `code/src/data/traits_try.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
    - `code/tests/unit/test_traits_fallback.py` — NOT invoked by the run-book
    - `code/tests/unit/test_traits_try.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/post_qc_species_list.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
