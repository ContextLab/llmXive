# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/feasibility_check.py: self-declared fabricated metric — “…the diffusion steps. Here we simulate      the latency impact by artificially introd…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/feasibility_check.py: self-declared fabricated metric — “…the diffusion steps. Here we simulate      the latency impact by artificially introd…”; 1 run-book script(s) missing (plan/impl path mismatch): python train.py --input data/processed/gsm8k_features.jsonl --target B_star --models xgboost,random_forest,decision_tree --split 0.8 --task classification; 3 command(s) failed: python code/sweep.py --dataset gsmk --block-sizes 1,2,4,8,16,32 --samples 500 --seed 42 (rc=1); python code/features.py --dataset gsm8k --input data/processed/gsm8k_ground_truth.jsonl --output data/processed/gsm8k_features.jsonl (rc=1); python code/evaluate.py --models data/models/ --test-data data/processed/humaneval_features.jsonl --metrics accuracy,f1,correlation,generalization (rc=1)

## Failing / missing run-book commands

- python code/sweep.py --dataset gsmk --block-sizes 1,2,4,8,16,32 --samples 500 --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/sweep.py", line 13, in <module>
    from utils.data_loader import load_gsm8k_streaming, load_humaneval_streaming
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/utils/data_loader.py", line 2, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/features.py --dataset gsm8k --input data/processed/gsm8k_ground_truth.jsonl --output data/processed/gsm8k_features.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/features.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python train.py --input data/processed/gsm8k_features.jsonl --target B_star --models xgboost,random_forest,decision_tree --split 0.8 --task classification -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/train.py': [Errno 2] No such file or directory
- python code/evaluate.py --models data/models/ --test-data data/processed/humaneval_features.jsonl --metrics accuracy,f1,correlation,generalization -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/evaluate.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
