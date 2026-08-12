# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/download/adni_downloader.py: self-declared fabricated metric — “…bject_list:                 # Placeholder values - in production, these would…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/download/adni_downloader.py: self-declared fabricated metric — “…bject_list:                 # Placeholder values - in production, these would…”; 1 command(s) failed: python code/main.py (rc=1); 5 declared deliverable(s) absent: data/analysis/centrality_metrics.csv; data/analysis/diagnostics.json; data/analysis/qc_log.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-299-assessing-the-impact-of-network-centrali/code/main.py", line 17, in <module>
    from code.main_us1 import run_us1_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-299-assessing-the-impact-of-network-centrali/code/main_us1.py", line 18, in <module>
    from code.download.adni_downloader import run_downloader
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-299-assessing-the-impact-of-network-centrali/code/download/adni_downloader.py", line 18, in <module>
    from code.utils.logging_config import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-299-assessing-the-impact-of-network-centrali/code/utils/logging_config.py", line 51, in <module>
    def log_event(logger: logging.Logger, event: str, data: Optional[Dict[str, Any]] = None):
                                                                     ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

## Declared deliverables still missing

- data/analysis/centrality_metrics.csv
- data/analysis/diagnostics.json
- data/analysis/qc_log.json
- data/analysis/regression_results.csv
- data/raw/participant_list.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/centrality_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/data_models.py` — NOT invoked by the run-book
    - `code/analysis/data_merger.py` — NOT invoked by the run-book
    - `code/centrality/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/centrality_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/main_us2.py` — NOT invoked by the run-book
    - `code/analysis/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/qc_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/analysis/qc_validator.py` — NOT invoked by the run-book
    - `code/centrality/metrics.py` — NOT invoked by the run-book
    - `code/centrality/connectivity.py` — NOT invoked by the run-book
    - `code/preprocess/fMRI_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/qc_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/regression_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main_us2.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/diagnostics.py` — NOT invoked by the run-book
    - `code/viz/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/regression_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participant_list.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/download/adni_downloader.py` — NOT invoked by the run-book
    - `code/preprocess/fMRI_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/participant_list.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
