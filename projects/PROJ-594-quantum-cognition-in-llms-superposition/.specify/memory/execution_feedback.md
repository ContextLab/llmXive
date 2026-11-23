# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/bert_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…ses=2)          # Create dummy input     batch_size = 4     s…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/models/bert_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…ses=2)          # Create dummy input     batch_size = 4     s…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/experiments/run_ablation.py --seed 42; 5 command(s) failed: python code/data/download_wic.py (rc=1); python code/experiments/run_baseline.py --seed 42 (rc=1); python code/experiments/run_quantum.py --seed 42 (rc=1); 5 declared deliverable(s) absent: data/results/ablation_metrics.json; data/results/baseline_metrics.json; data/results/interference_correlation.json

## Failing / missing run-book commands

- python code/data/download_wic.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/data/download_wic.py", line 23, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/experiments/run_baseline.py --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/experiments/run_baseline.py", line 5, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/experiments/run_quantum.py --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/experiments/run_quantum.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/experiments/run_ablation.py --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/experiments/run_ablation.py': [Errno 2] No such file or directory
- python code/analysis/stats_test.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/analysis/stats_test.py", line 9, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/interference_check.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-594-quantum-cognition-in-llms-superposition/code/analysis/interference_check.py", line 14, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

## Declared deliverables still missing

- data/results/ablation_metrics.json
- data/results/baseline_metrics.json
- data/results/interference_correlation.json
- data/results/quantum_metrics.json
- data/results/stats_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/ablation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/verify_ablation_interference.py` — NOT invoked by the run-book
    - `code/experiments/generate_ablation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ablation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/baseline_bert.py` — NOT invoked by the run-book
    - `code/analysis/stats_test.py` — IS a run-book command
    - `code/experiments/run_stats.py` — NOT invoked by the run-book
    - `code/experiments/generate_ablation_metrics.py` — NOT invoked by the run-book
    - `code/experiments/run_baseline.py` — IS a run-book command
    - `code/experiments/run_classical_baseline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/interference_correlation.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/interference_check.py` — IS a run-book command
  Make ONE of these WRITE `data/results/interference_correlation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/quantum_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats_test.py` — IS a run-book command
    - `code/experiments/run_quantum.py` — IS a run-book command
    - `code/experiments/run_stats.py` — NOT invoked by the run-book
    - `code/experiments/generate_ablation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/quantum_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/stats_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/verify_stats_report.py` — NOT invoked by the run-book
    - `code/analysis/stats_test.py` — IS a run-book command
    - `code/experiments/run_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stats_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
