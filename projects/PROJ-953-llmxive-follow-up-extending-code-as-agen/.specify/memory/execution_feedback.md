# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/extract_features.py: self-declared fabricated metric — “…s         # For now, return a dummy value or None to trigger fallback…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/extract_features.py: self-declared fabricated metric — “…s         # For now, return a dummy value or None to trigger fallback…”; 1 run-book script(s) missing (plan/impl path mismatch): python scripts/evaluate.py --model models/model.pkl --results data/processed/model_results.csv; 4 command(s) failed: python code/scripts/ingest.py --sample-size 100 --mode pilot (rc=1); python code/scripts/ingest.py --sample-size 500 --timeout 600 (rc=1); python code/scripts/train_model.py --input data/processed/features.csv --thresholds 0.01,0.05,0.1 (rc=1); 5 declared deliverable(s) absent: data/processed/features.csv; data/processed/ground_truth.csv; data/processed/model_report.json

## Failing / missing run-book commands

- python code/scripts/ingest.py --sample-size 100 --mode pilot -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/ingest.py", line 13, in <module>
    from scripts.config import SAMPLE_SIZE
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/config.py", line 53, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable 'HF_TOKEN'. Set it to a valid HuggingFace access token before running the pipeline.

- python code/scripts/ingest.py --sample-size 500 --timeout 600 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/ingest.py", line 13, in <module>
    from scripts.config import SAMPLE_SIZE
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/config.py", line 53, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable 'HF_TOKEN'. Set it to a valid HuggingFace access token before running the pipeline.

- python code/scripts/train_model.py --input data/processed/features.csv --thresholds 0.01,0.05,0.1 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/train_model.py", line 15, in <module>
    from config.loader import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/config.py", line 53, in <module>
    raise RuntimeError(
RuntimeError: Missing required environment variable 'HF_TOKEN'. Set it to a valid HuggingFace access token before running the pipeline.

- python scripts/evaluate.py --model models/model.pkl --results data/processed/model_results.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-953-llmxive-follow-up-extending-code-as-agen/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/scripts/evaluate.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
date_features import (
E   ImportError: cannot import name 'REQUIRED_COLUMNS' from 'validate_features' (/home/runner/work/llmXive/llmXive/projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/scripts/validate_features.py)
=========================== short test summary info ============================
ERROR tests/contract/test_ingest.py - RuntimeError: Missing required environm...
ERROR tests/unit/test_config.py
ERROR tests/unit/test_config_loader.py
ERROR tests/unit/test_edge_cases.py - RuntimeError: Missing required environm...
ERROR tests/unit/test_ingest_parsing.py - RuntimeError: Missing required envi...
ERROR tests/unit/test_ingest_syntax_validation.py - RuntimeError: Missing req...
ERROR tests/unit/test_performance_constraints.py - RuntimeError: Missing requ...
ERROR tests/unit/test_performance_optimization.py - RuntimeError: Missing req...
ERROR tests/unit/test_profile_pipeline.py - RuntimeError: Missing required en...
ERROR tests/unit/test_safety_evaluation.py
ERROR tests/unit/test_validate_features.py
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 1 skipped, 11 errors in 1.97s =========================



## Declared deliverables still missing

- data/processed/features.csv
- data/processed/ground_truth.csv
- data/processed/model_report.json
- data/processed/raw_outcomes.json
- data/processed/threshold_sweep.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/calculate_correlations.py` — NOT invoked by the run-book
    - `code/scripts/checksum_artifacts.py` — NOT invoked by the run-book
    - `code/scripts/finalize_features.py` — NOT invoked by the run-book
    - `code/scripts/generate_features.py` — NOT invoked by the run-book
    - `code/scripts/optimization_guide.py` — NOT invoked by the run-book
    - `code/scripts/profile_pipeline.py` — NOT invoked by the run-book
    - `code/scripts/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/scripts/train_model.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/baseline_runner.py` — NOT invoked by the run-book
    - `code/scripts/calculate_correlations.py` — NOT invoked by the run-book
    - `code/scripts/checksum_artifacts.py` — NOT invoked by the run-book
    - `code/scripts/extract_features.py` — IS a run-book command
    - `code/scripts/finalize_features.py` — NOT invoked by the run-book
    - `code/scripts/generate_features.py` — NOT invoked by the run-book
    - `code/scripts/generate_ground_truth.py` — NOT invoked by the run-book
    - `code/scripts/optimization_guide.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/checksum_artifacts.py` — NOT invoked by the run-book
    - `code/scripts/generate_model_report.py` — NOT invoked by the run-book
    - `code/scripts/optimization_guide.py` — NOT invoked by the run-book
    - `code/scripts/train_model.py` — IS a run-book command
    - `code/scripts/verify_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_outcomes.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/baseline_runner.py` — NOT invoked by the run-book
    - `code/scripts/verify_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_outcomes.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/checksum_artifacts.py` — NOT invoked by the run-book
    - `code/scripts/generate_model_report.py` — NOT invoked by the run-book
    - `code/scripts/identify_threshold.py` — NOT invoked by the run-book
    - `code/scripts/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/scripts/train_model.py` — IS a run-book command
    - `code/scripts/verify_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
