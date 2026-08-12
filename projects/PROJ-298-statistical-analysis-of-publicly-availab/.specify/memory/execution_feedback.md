# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/setup_data_structure.py: self-declared fabricated metric — “…s is REAL data structure, not fake values)     # Source: https://surve…”
- code/analysis/trends.py: synthetic/fake INPUT data not authorized by the spec — “…erations):             # Generate synthetic series with this slope…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…ny fallback to synthetic/mock data. - Raises ConnectionErro…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/setup_data_structure.py: self-declared fabricated metric — “…s is REAL data structure, not fake values)     # Source: https://surve…”; code/analysis/trends.py: synthetic/fake INPUT data not authorized by the spec — “…erations):             # Generate synthetic series with this slope…”; code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…ny fallback to synthetic/mock data. - Raises ConnectionErro…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python code/data/download.py (rc=1); 10 declared deliverable(s) absent: data/processed/cluster_alignment.json; data/processed/cluster_results.json; data/processed/confidence_interval.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-298-statistical-analysis-of-publicly-availab/code/data/download.py", line 17, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-298-statistical-analysis-of-publicly-availab/code/data/download.py", line 19, in <module>
    raise ImportError(
ImportError: The 'datasets' package is required for streaming data. Please install it via: pip install datasets
- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-298-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-298-statistical-analysis-of-publicly-availab/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/cluster_alignment.json
- data/processed/cluster_results.json
- data/processed/confidence_interval.json
- data/processed/correlation_results.json
- data/processed/decomposition_intermediate.json
- data/processed/decomposition_results.json
- data/processed/external_metrics.json
- data/processed/tag_mappings.json
- data/processed/trend_intermediate.json
- data/processed/trend_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cluster_alignment.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_cluster_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_alignment.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cluster_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_cluster_results.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/confidence_interval.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/confidence_interval.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/decomposition_intermediate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_decomposition_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/decomposition_intermediate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/decomposition_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_decomposition_results.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/analysis/decomposition.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/decomposition_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/mapping.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
    - `code/data/external.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tag_mappings.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/mapping.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tag_mappings.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trend_intermediate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/trends.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trend_intermediate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trend_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
    - `code/data/external.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trend_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
