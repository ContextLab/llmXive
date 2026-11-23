# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/power.py: self-declared fabricated metric — “…pproximation formula     # or hard-coded values for the specific n=3 case wh…”
- code/data/generate_synthetic.py: self-declared fabricated metric — “…ulate variety     # These are NOT real measurements, just deterministic patterns…”
- code/analysis/ground_state.py: synthetic/fake INPUT data not authorized by the spec — “…t     silent fallback to synthetic data.      Returns:         D…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generation Module. Imple…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…Constraint: This module generates DETERMINISTIC synthetic data for CI logic testin…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…) -> tuple:     """     Generate a deterministic synthetic decay curve.     Uses a…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…th) -> None:     """     Generate synthetic transient-absorption tra…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…1          logger.info(f"Generated synthetic traces to {output_path}"…”

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/main.py --mode simulate`
- `python code/main.py --mode real --data-path data/raw/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 26 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/power.py: self-declared fabricated metric — “…pproximation formula     # or hard-coded values for the specific n=3 case wh…”; code/data/generate_synthetic.py: self-declared fabricated metric — “…ulate variety     # These are NOT real measurements, just deterministic patterns…”; code/analysis/ground_state.py: synthetic/fake INPUT data not authorized by the spec — “…t     silent fallback to synthetic data.      Returns:         D…”; 3 command(s) failed: python code/main.py --mode simulate (rc=1); python code/main.py --mode real --data-path data/raw/ (rc=1); python -m pytest tests/ (rc=1); 8 declared deliverable(s) absent: data/compute/solvent_solvation.csv; data/processed/compliance_report.json; data/processed/environment_logs.json

## Failing / missing run-book commands

- python code/main.py --mode simulate -> rc=1
-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791625855.441659    5518 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
E0000 00:00:1791625856.830622    5518 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
TensorFlow GPU devices disabled via config.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 25, in <module>
    from data.loaders import get_all_solvents, get_solvent_properties, SolventDataError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/data/loaders.py", line 13, in <module>
    from utils.logging import log_compliance_check
ImportError: cannot import name 'log_compliance_check' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/utils/logging.py)

- python code/main.py --mode real --data-path data/raw/ -> rc=1
-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1791625861.390427    5527 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
E0000 00:00:1791625862.817856    5527 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
TensorFlow GPU devices disabled via config.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 25, in <module>
    from data.loaders import get_all_solvents, get_solvent_properties, SolventDataError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/data/loaders.py", line 13, in <module>
    from utils.logging import log_compliance_check
ImportError: cannot import name 'log_compliance_check' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/utils/logging.py)

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/compute/solvent_solvation.csv
- data/processed/compliance_report.json
- data/processed/environment_logs.json
- data/processed/kinetic_metrics.csv
- data/processed/sensitivity_analysis.csv
- data/processed/study_power_analysis.json
- data/processed/validation_flags.json
- data/raw/synthetic_traces.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/compute/solvent_solvation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/data/compute/solvent_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/compute/solvent_solvation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/compliance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/compliance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/compliance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/environment_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/environment.py` — NOT invoked by the run-book
    - `code/analysis/material_balance.py` — NOT invoked by the run-book
    - `code/analysis/method_spec.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/environment_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/kinetic_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/detection_threshold.py` — NOT invoked by the run-book
    - `code/analysis/error_propagation.py` — NOT invoked by the run-book
    - `code/analysis/kinetic_fit.py` — NOT invoked by the run-book
    - `code/analysis/kinetic_metrics.py` — NOT invoked by the run-book
    - `code/analysis/method_spec.py` — NOT invoked by the run-book
    - `code/analysis/replicate_dashboard.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/kinetic_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/study_power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/run_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/study_power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_flags.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/compliance.py` — NOT invoked by the run-book
    - `code/analysis/ground_state.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_flags.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/kinetic_fit.py` — NOT invoked by the run-book
    - `code/data/generate_synthetic.py` — NOT invoked by the run-book
    - `code/hardware/interface.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/synthetic_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
