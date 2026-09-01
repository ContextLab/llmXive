# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/ground_state.py: synthetic/fake INPUT data not authorized by the spec — “…t     silent fallback to synthetic data.      Returns:         D…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ion Traces.  This module generates deterministic synthetic transient-absorption tra…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…np.ndarray:     """     Generate a synthetic exponential decay curve…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…se ) -> str:     """     Generate synthetic transient-absorption tra…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…try point for generating synthetic data.     """     parser = ar…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate deterministic synthetic transient-absorption tra…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…arning(                 "Synthetic data file already exists. "…”
- code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…e --bypass-real-check to generate synthetic data. "…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 23 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/ground_state.py: synthetic/fake INPUT data not authorized by the spec — “…t     silent fallback to synthetic data.      Returns:         D…”; code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ion Traces.  This module generates deterministic synthetic transient-absorption tra…”; code/data/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…np.ndarray:     """     Generate a synthetic exponential decay curve…”; 2 command(s) failed: python code/main.py --mode simulate (rc=1); python code/main.py --mode real --data-path data/raw/ (rc=1); 4 declared deliverable(s) absent: data/compute/solvent_solvation.csv; data/processed/environment_logs.json; data/processed/kinetic_metrics.csv

## Failing / missing run-book commands

- python code/main.py --mode simulate -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 36, in <module>
    from data.loaders import get_solvent_properties, get_all_solvents, get_dielectric_constant_range, SolventDataError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/data/loaders.py", line 10, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --mode real --data-path data/raw/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/main.py", line 36, in <module>
    from data.loaders import get_solvent_properties, get_all_solvents, get_dielectric_constant_range, SolventDataError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/code/data/loaders.py", line 10, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/compute/solvent_solvation.csv
- data/processed/environment_logs.json
- data/processed/kinetic_metrics.csv
- data/raw/synthetic_traces.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/compute/solvent_solvation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/data/compute/solvent_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/compute/solvent_solvation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/environment_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/method_spec.py` — NOT invoked by the run-book
    - `code/analysis/environment.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/environment_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/kinetic_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/method_spec.py` — NOT invoked by the run-book
    - `code/analysis/detection_threshold.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/replicate_dashboard.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/analysis/error_propagation.py` — NOT invoked by the run-book
    - `code/analysis/kinetic_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/kinetic_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_traces.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/kinetic_fit.py` — NOT invoked by the run-book
    - `code/hardware/interface.py` — NOT invoked by the run-book
    - `code/data/generate_synthetic.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_traces.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
