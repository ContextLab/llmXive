# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/stats_engine.py: synthetic/fake INPUT data not authorized by the spec — “…ames for unit‑tests that generate synthetic data. """  import os imp…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv`
  - script usage: `graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUT] [--out OUT]`
  - argparse error: `graph_builder.py: error: unrecognized arguments: --backend ibmq_manila`
- run-book command: `python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv`
  - script usage: `graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUT] [--out OUT]`
  - argparse error: `graph_builder.py: error: unrecognized arguments: --backend ibmq_manila`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/stats_engine.py: synthetic/fake INPUT data not authorized by the spec — “…ames for unit‑tests that generate synthetic data. """  import os imp…”; 4 command(s) failed: python -m pytest tests/test_stats_engine.py -v (rc=2); python -m pytest tests/test_integration_fetch.py -v   # live API (rate‑limited) (rc=4); python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv (rc=2); 5 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/mdes_report.json; data/processed/partial_correlations.csv

## Failing / missing run-book commands

- python -m pytest tests/test_stats_engine.py -v -> rc=2
1-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/test_stats_engine.py:19: in <module>
    from code.stats_engine import (
code/stats_engine.py:23: in <module>
    import statsmodels.api as sm
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/api.py:76: in <module>
    from . import datasets, distributions, iolib, regression, robust, tools
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/distributions/__init__.py:7: in <module>
    from .discrete import (
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/distributions/discrete.py:5: in <module>
    from scipy._lib._util import _lazywhere
E   ImportError: cannot import name '_lazywhere' from 'scipy._lib._util' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-163-exploring-the-role-of-network-structure-/lib/python3.11/site-packages/scipy/_lib/_util.py)
=========================== short test summary info ============================
ERROR tests/test_stats_engine.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.95s ===============================


- python -m pytest tests/test_integration_fetch.py -v   # live API (rate‑limited) -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-163-exploring-the-role-of-network-structure-/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv -> rc=2

usage: graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUT] [--out OUT]
                        [--generate-metrics]
graph_builder.py: error: unrecognized arguments: --backend ibmq_manila

- python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv -> rc=2

usage: graph_builder.py [-h] [--raw-dir RAW_DIR] [--output OUT] [--out OUT]
                        [--generate-metrics]
graph_builder.py: error: unrecognized arguments: --backend ibmq_manila


## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/mdes_report.json
- data/processed/partial_correlations.csv
- data/processed/robustness_results.csv
- figures/correlation_heatmap.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_mdes_report_section.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mdes_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_mdes_report_section.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mdes_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/partial_correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/partial_correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/correlation_heatmap.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/correlation_heatmap.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
