# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/generate_sensitivity_report.py: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”
- code/research.md: synthetic/fake INPUT data not authorized by the spec — “…correlations within the simulated data. - **Role**: The algorit…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/generate_sensitivity_report.py: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”; code/research.md: synthetic/fake INPUT data not authorized by the spec — “…correlations within the simulated data. - **Role**: The algorit…”; 3 command(s) failed: python code/main.py --mode single --N 1000 --theta 2.5 --k 1 --pattern diagonal (rc=1); python code/main.py --mode sweep --N 2000 --iterations 100 --patterns diagonal,block-sparse,random-sparse (rc=1); python code/main.py --mode sensitivity --N 1000 --theta 1.5 --densities 0.1,0.2,0.3 (rc=1); 10 declared deliverable(s) absent: data/figures/outlier_probability_vs_theta.png; data/processed/convergence_data.json; data/processed/mc_results.csv

## Failing / missing run-book commands

- python code/main.py --mode single --N 1000 --theta 2.5 --k 1 --pattern diagonal -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/code/main.py", line 14, in <module>
    from utils.config import load_config, ensure_directories
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/code/utils/config.py)
- python code/main.py --mode sweep --N 2000 --iterations 100 --patterns diagonal,block-sparse,random-sparse -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/code/main.py", line 14, in <module>
    from utils.config import load_config, ensure_directories
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/code/utils/config.py)
- python code/main.py --mode sensitivity --N 1000 --theta 1.5 --densities 0.1,0.2,0.3 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/code/main.py", line 14, in <module>
    from utils.config import load_config, ensure_directories
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/code/utils/config.py)

## Declared deliverables still missing

- data/figures/outlier_probability_vs_theta.png
- data/processed/convergence_data.json
- data/processed/mc_results.csv
- data/processed/sensitivity_density_sweep.csv
- data/processed/sensitivity_metadata.json
- data/processed/sensitivity_variation.csv
- data/processed/single_run_results.json
- data/processed/threshold_identification.json
- data/processed/threshold_sweep_results.csv
- data/processed/validated_sweep_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/figures/outlier_probability_vs_theta.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plot_outlier_probability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/figures/outlier_probability_vs_theta.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/convergence_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/threshold_sweep.py` — NOT invoked by the run-book
    - `code/analysis/threshold_sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/convergence_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mc_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/threshold_sweep.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis_runner.py` — NOT invoked by the run-book
    - `code/analysis/monte_carlo_runner.py` — NOT invoked by the run-book
    - `code/analysis/validate_sweep_results.py` — NOT invoked by the run-book
    - `code/analysis/fit_utils.py` — NOT invoked by the run-book
    - `code/analysis/threshold_sweep_runner.py` — NOT invoked by the run-book
    - `code/analysis/threshold_identification_raw.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mc_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_density_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_metadata_recorder.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_density_sweep.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_variation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_density_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_metadata_recorder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_variation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_variation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_variation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/single_run_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/results_logger.py` — NOT invoked by the run-book
    - `code/analysis/task019b_traceability.py` — NOT invoked by the run-book
    - `code/analysis/simulation_loop.py` — NOT invoked by the run-book
    - `code/analysis/results_recorder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/single_run_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_identification.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/threshold_sweep_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/critical_threshold_report.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis_runner.py` — NOT invoked by the run-book
    - `code/analysis/threshold_fit_params.py` — NOT invoked by the run-book
    - `code/analysis/fit_utils.py` — NOT invoked by the run-book
    - `code/analysis/threshold_identification_raw.py` — NOT invoked by the run-book
    - `code/analysis/threshold_identification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_identification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_sweep_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/threshold_sweep_aggregator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_fit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_sweep_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validated_sweep_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/critical_threshold_report.py` — NOT invoked by the run-book
    - `code/analysis/validate_sweep_results.py` — NOT invoked by the run-book
    - `code/analysis/plot_outlier_probability.py` — NOT invoked by the run-book
    - `code/analysis/fit_utils.py` — NOT invoked by the run-book
    - `code/analysis/threshold_identification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validated_sweep_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
