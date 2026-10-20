# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/sensitivity_analysis.py: self-declared fabricated metric — “…this iteration to avoid empty/fake results.             logger.warning(…”
- code/strategies/noisy_baseline_runner.py: self-declared fabricated metric — “…nce.")             # Return a placeholder result for testing without model…”
- code/analysis/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…the task implies we must generate synthetic sensitivity curves…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/sensitivity_analysis.py: self-declared fabricated metric — “…this iteration to avoid empty/fake results.             logger.warning(…”; code/strategies/noisy_baseline_runner.py: self-declared fabricated metric — “…nce.")             # Return a placeholder result for testing without model…”; code/analysis/sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…the task implies we must generate synthetic sensitivity curves…”; overall deadline 300s exceeded; 1 command(s) failed: python code/scripts/download_locomo.py (rc=1); 11 declared deliverable(s) absent: data/intermediate/graphs_raw.json; data/processed/baseline_results.csv; data/processed/greedy_results.csv

## Failing / missing run-book commands

- python code/scripts/download_locomo.py -> rc=1
/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/scripts/download_locomo.py", line 18, in <module>
    from data_loader import load_locomo_strict, ensure_output_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 23, in <module>
    from datasets import load_dataset, DatasetDict
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-894-llmxive-follow-up-extending-memory-is-re/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.3


## Declared deliverables still missing

- data/intermediate/graphs_raw.json
- data/processed/baseline_results.csv
- data/processed/greedy_results.csv
- data/processed/lazy_results.csv
- data/processed/noisy_baseline_results.csv
- data/processed/noisy_lazy_results.csv
- data/processed/report_data.json
- data/processed/sensitivity_analysis.json
- data/processed/stats_clean.json
- data/processed/stats_noisy.json
- data/raw/locomo.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/intermediate/graphs_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/run_greedy.py` — NOT invoked by the run-book
    - `code/run_lazy.py` — NOT invoked by the run-book
    - `code/runner.py` — NOT invoked by the run-book
    - `code/scripts/generate_noisy_graphs.py` — NOT invoked by the run-book
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/verify_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/graphs_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
    - `code/run_greedy.py` — NOT invoked by the run-book
    - `code/strategies/greedy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
    - `code/run_noisy_baseline.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/categorize_status_counts.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/report_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/report/aggregate_results.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/report_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/strategies/lazy.py` — NOT invoked by the run-book
    - `code/strategies/sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stats_clean.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stats_clean.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stats_noisy.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stats_noisy.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/locomo.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/run_lazy.py` — NOT invoked by the run-book
    - `code/run_noisy_baseline.py` — NOT invoked by the run-book
    - `code/scripts/download_locomo.py` — IS a run-book command
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/locomo.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
