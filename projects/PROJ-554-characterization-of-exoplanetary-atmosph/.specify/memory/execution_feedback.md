# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “….          Logic:     1. Generate 1000 synthetic datasets with a known tr…”
- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…We need a generator for synthetic data with a specific correlat…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “….          Logic:     1. Generate 1000 synthetic datasets with a known tr…”; code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…We need a generator for synthetic data with a specific correlat…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 command(s) failed: python code/download.py --output data/raw (rc=1); python code/retrieval.py --input data/raw --output data/processed (rc=1); python code/analysis.py --input data/processed/analysis_dataset.csv --output results (rc=1); 6 declared deliverable(s) absent: data/processed/analysis_results.json; data/processed/bootstrap_ci.json; data/processed/correlation_stats.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-554-characterization-of-exoplanetary-atmosph/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/main.py': [Errno 2] No such file or directory

- python code/download.py --output data/raw -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 11, in <module>
    from config import get_config, Configuration
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/config.py", line 8, in <module>
    from utils import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/utils.py", line 137, in <module>
    def create_censored_series(series: pd.Series, threshold: Optional[float] = None) -> pd.Series:
                                       ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python code/retrieval.py --input data/raw --output data/processed -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 9, in <module>
    from config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/config.py", line 8, in <module>
    from utils import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/utils.py", line 137, in <module>
    def create_censored_series(series: pd.Series, threshold: Optional[float] = None) -> pd.Series:
                                       ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python code/analysis.py --input data/processed/analysis_dataset.csv --output results -> rc=1

WARNING:root:sksurv not available. Kendall's tau calculation will use a simplified rank-based approximation.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/analysis.py", line 25, in <module>
    from config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/config.py", line 8, in <module>
    from utils import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/utils.py", line 137, in <module>
    def create_censored_series(series: pd.Series, threshold: Optional[float] = None) -> pd.Series:
                                       ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?


## Declared deliverables still missing

- data/processed/analysis_results.json
- data/processed/bootstrap_ci.json
- data/processed/correlation_stats.json
- data/processed/metadata.csv
- data/processed/regression_results.json
- data/processed/retrieval_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/instrument_calibration.py` — NOT invoked by the run-book
    - `code/noise_stability.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bootstrap_ci.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_stats.py` — NOT invoked by the run-book
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bootstrap_ci.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_stats.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/analysis_tobit.py` — NOT invoked by the run-book
    - `code/detection_limit_analysis.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
    - `code/instrument_calibration.py` — NOT invoked by the run-book
    - `code/noise_stability.py` — NOT invoked by the run-book
    - `code/plots.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/analysis_tobit.py` — NOT invoked by the run-book
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/regression_stats.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/retrieval_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/analysis_tobit.py` — NOT invoked by the run-book
    - `code/detection_limit_analysis.py` — NOT invoked by the run-book
    - `code/instrument_calibration.py` — NOT invoked by the run-book
    - `code/mdc_stats.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/plots_noise_signal.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/retrieval_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
