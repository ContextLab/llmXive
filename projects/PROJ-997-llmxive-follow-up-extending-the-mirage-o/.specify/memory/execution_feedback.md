# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/cli/run_proxy_loop.py: self-declared fabricated metric — “…on't have logits here,     we simulate the score based on the correctness of t…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/cli/run_proxy_loop.py: self-declared fabricated metric — “…on't have logits here,     we simulate the score based on the correctness of t…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/models/train_predictor.py  --data data/processed/training_sample.parquet  --model_out data/models/gap_predictor.pkl  --seed 42; python code/models/evaluate_predictor.py  --model data/models/gap_predictor.pkl  --data data/processed/training_sample.parquet  --metrics_out data/metrics/metrics.json  --predictions_out data/metrics/gap_predictions.parquet; python code/validation/mipu_benchmark.py  --model data/models/gap_predictor.pkl  --data data/processed/training_sample.parquet  --output data/metrics/benchmark_report.json; 3 command(s) failed: python code/cli/generate_ground_truth.py  --model meta-llama/Meta-Llama-2-7B-4bit  --quant_levels INT4 INT8 FP8  --prompt_source gsm8k  --output data/processed/training_sample.parquet  --seed 42 (rc=1); python code/cli/validate_dataset_stats.py  --input data/processed/training_sample.parquet  --output data/metrics/dataset_stats.json (rc=1); python -m pytest -m contract (rc=2); 2 declared deliverable(s) absent: data/metrics/dataset_stats.json; data/processed/training_sample.parquet

## Failing / missing run-book commands

- python code/cli/generate_ground_truth.py  --model meta-llama/Meta-Llama-2-7B-4bit  --quant_levels INT4 INT8 FP8  --prompt_source gsm8k  --output data/processed/training_sample.parquet  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_ground_truth.py", line 35, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/cli/validate_dataset_stats.py  --input data/processed/training_sample.parquet  --output data/metrics/dataset_stats.json -> rc=1

Failed to read training data parquet: Parquet file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/processed/training_sample.parquet

- python code/models/train_predictor.py  --data data/processed/training_sample.parquet  --model_out data/models/gap_predictor.pkl  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-997-llmxive-follow-up-extending-the-mirage-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/models/train_predictor.py': [Errno 2] No such file or directory

- python code/models/evaluate_predictor.py  --model data/models/gap_predictor.pkl  --data data/processed/training_sample.parquet  --metrics_out data/metrics/metrics.json  --predictions_out data/metrics/gap_predictions.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-997-llmxive-follow-up-extending-the-mirage-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/models/evaluate_predictor.py': [Errno 2] No such file or directory

- python code/validation/mipu_benchmark.py  --model data/models/gap_predictor.pkl  --data data/processed/training_sample.parquet  --output data/metrics/benchmark_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-997-llmxive-follow-up-extending-the-mirage-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/validation/mipu_benchmark.py': [Errno 2] No such file or directory

- python code/cli/measure_runtime.py  --pipeline "full"  --output data/metrics/runtime.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-997-llmxive-follow-up-extending-the-mirage-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/measure_runtime.py': [Errno 2] No such file or directory

- python -m pytest -m contract -> rc=2
xt.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_data_generation.py
ERROR tests/integration/test_generate_dataset.py
ERROR tests/integration/test_generate_dataset_core.py
ERROR tests/integration/test_generate_dataset_stream.py
ERROR tests/integration/test_model_training.py
ERROR tests/integration/test_validation.py
ERROR tests/integration/test_verify_dataset_completeness.py
ERROR tests/unit/test_audit_data_integrity.py
ERROR tests/unit/test_bound_verifier.py
ERROR tests/unit/test_extract_features.py
ERROR tests/unit/test_gap_calculator.py
ERROR tests/unit/test_generate_visualization_report.py
ERROR tests/unit/test_latency_meter.py
ERROR tests/unit/test_train_predictor.py
ERROR tests/unit/test_verify_model_availability.py
ERROR tests/unit/test_verify_model_robustness.py
!!!!!!!!!!!!!!!!!!! Interrupted: 16 errors during collection !!!!!!!!!!!!!!!!!!!
================ 50 deselected, 13 warnings, 16 errors in 2.52s ================



## Declared deliverables still missing

- data/metrics/dataset_stats.json
- data/processed/training_sample.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/dataset_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/cli/validate_dataset_stats.py` — IS a run-book command
    - `code/data/generate_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/dataset_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/training_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/cli/audit_data_integrity.py` — NOT invoked by the run-book
    - `code/cli/generate_ground_truth.py` — IS a run-book command
    - `code/cli/generate_visualization_report.py` — NOT invoked by the run-book
    - `code/cli/validate_dataset_stats.py` — IS a run-book command
    - `code/src/cli/generate_dataset.py` — NOT invoked by the run-book
    - `code/src/cli/run_proxy_loop.py` — NOT invoked by the run-book
    - `code/src/cli/validate_features_diagnostic.py` — NOT invoked by the run-book
    - `code/src/services/latency_meter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/training_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
