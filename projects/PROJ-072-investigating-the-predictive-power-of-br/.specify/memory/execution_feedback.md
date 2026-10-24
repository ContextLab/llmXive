# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/classification/run_sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…al data. Proceeding with simulated data.")         else:…”
- code/classification/run_sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…ilable in original data. Simulated data might be redundant but p…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/classification/run_sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…al data. Proceeding with simulated data.")         else:…”; code/classification/run_sensitivity_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…ilable in original data. Simulated data might be redundant but p…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/preprocessing/download_check.py; 4 command(s) failed: python code/main.py --mode preprocess --subset 5 (rc=1); python code/main.py --mode extract_features (rc=1); python code/main.py --mode classify --permutations 1000 (rc=1); 6 declared deliverable(s) absent: data/metadata/analysis_config.json; data/metadata/subject_labels.csv; data/processed/features.csv

## Failing / missing run-book commands

- python code/preprocessing/download_check.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-072-investigating-the-predictive-power-of-br/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-072-investigating-the-predictive-power-of-br/code/preprocessing/download_check.py': [Errno 2] No such file or directory

- python code/main.py --mode preprocess --subset 5 -> rc=1
2026-10-24 03:32:05,038 - INFO - Pipeline Orchestrator started at 2026-10-24T03:32:05.038254
2026-10-24 03:32:05,038 - INFO - Maximum runtime limit: 21600 seconds (6 hours)
2026-10-24 03:32:05,038 - INFO - Checking for data gaps...
2026-10-24 03:32:05,038 - WARNING - DATA_GAP: Raw data directory 'data/raw/ds000030' not found.
2026-10-24 03:32:05,038 - WARNING - Please run the download task (T011) before proceeding.
2026-10-24 03:32:05,038 - CRITICAL - Stopping due to DATA_GAP condition.


- python code/main.py --mode extract_features -> rc=1
2026-10-24 03:32:05,062 - INFO - Pipeline Orchestrator started at 2026-10-24T03:32:05.062511
2026-10-24 03:32:05,062 - INFO - Maximum runtime limit: 21600 seconds (6 hours)
2026-10-24 03:32:05,062 - INFO - Checking for data gaps...
2026-10-24 03:32:05,062 - WARNING - DATA_GAP: Raw data directory 'data/raw/ds000030' not found.
2026-10-24 03:32:05,062 - WARNING - Please run the download task (T011) before proceeding.
2026-10-24 03:32:05,062 - CRITICAL - Stopping due to DATA_GAP condition.


- python code/main.py --mode classify --permutations 1000 -> rc=1
2026-10-24 03:32:05,088 - INFO - Pipeline Orchestrator started at 2026-10-24T03:32:05.088158
2026-10-24 03:32:05,088 - INFO - Maximum runtime limit: 21600 seconds (6 hours)
2026-10-24 03:32:05,088 - INFO - Checking for data gaps...
2026-10-24 03:32:05,088 - WARNING - DATA_GAP: Raw data directory 'data/raw/ds000030' not found.
2026-10-24 03:32:05,088 - WARNING - Please run the download task (T011) before proceeding.
2026-10-24 03:32:05,088 - CRITICAL - Stopping due to DATA_GAP condition.


- python code/main.py --mode classify --random_labels -> rc=1
2026-10-24 03:32:05,113 - INFO - Pipeline Orchestrator started at 2026-10-24T03:32:05.113348
2026-10-24 03:32:05,113 - INFO - Maximum runtime limit: 21600 seconds (6 hours)
2026-10-24 03:32:05,113 - INFO - Checking for data gaps...
2026-10-24 03:32:05,113 - WARNING - DATA_GAP: Raw data directory 'data/raw/ds000030' not found.
2026-10-24 03:32:05,113 - WARNING - Please run the download task (T011) before proceeding.
2026-10-24 03:32:05,113 - CRITICAL - Stopping due to DATA_GAP condition.



## Declared deliverables still missing

- data/metadata/analysis_config.json
- data/metadata/subject_labels.csv
- data/processed/features.csv
- data/processed/features_cleaned.csv
- data/processed/features_sim_med.csv
- data/processed/sensitivity_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/analysis_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/classification/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/preprocessing/metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/analysis_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metadata/subject_labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/classification/cohen_d.py` — NOT invoked by the run-book
    - `code/classification/models.py` — NOT invoked by the run-book
    - `code/classification/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/graph_metrics/assemble_features.py` — NOT invoked by the run-book
    - `code/preprocessing/metadata.py` — NOT invoked by the run-book
    - `code/reports/generate_summary_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/subject_labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/classification/cohen_d.py` — NOT invoked by the run-book
    - `code/classification/models.py` — NOT invoked by the run-book
    - `code/classification/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/classification/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/classification/validation.py` — NOT invoked by the run-book
    - `code/graph_metrics/__init__.py` — NOT invoked by the run-book
    - `code/graph_metrics/assemble_features.py` — NOT invoked by the run-book
    - `code/graph_metrics/calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/classification/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_sim_med.csv` is declared but was NOT written. Scripts referencing it:
    - `code/classification/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/classification/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_sim_med.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/classification/run_sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
