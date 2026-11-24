# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/reports/summary.md: synthetic/fake INPUT data not authorized by the spec — “…nce of weight files. - **Synthetic Data**: **Strictly Prohibited…”
- code/scripts/generate_dummy_index.py: synthetic/fake INPUT data not authorized by the spec — “…red dependency file with dummy data. """ import os import sy…”
- code/src/evaluation/audit_data_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…and data/processed/ for synthetic data or placeholders. Confirm…”
- code/src/evaluation/audit_data_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…"""Audit a directory for synthetic data or placeholders."""…”
- src/evaluation/run_sensitivity_sweep.py: synthetic/fake INPUT data not authorized by the spec — “…# Since T022g generated synthetic pairs, we assume they ha…”
- src/ingestion/generate_synthetic_proxy.py: synthetic/fake INPUT data not authorized by the spec — “…""" T012c: Generate Synthetic Proxy for LoRA Weights.…”
- src/ingestion/generate_synthetic_proxy.py: synthetic/fake INPUT data not authorized by the spec — “…e status is "failed", it generates synthetic LoRA-like weight matrice…”
- src/ingestion/generate_synthetic_proxy.py: synthetic/fake INPUT data not authorized by the spec — “…c_weights():     """     Generate synthetic LoRA A and B matrices.…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 fabricated/simulated-result signal(s) — results are not real measurements: code/reports/summary.md: synthetic/fake INPUT data not authorized by the spec — “…nce of weight files. - **Synthetic Data**: **Strictly Prohibited…”; code/scripts/generate_dummy_index.py: synthetic/fake INPUT data not authorized by the spec — “…red dependency file with dummy data. """ import os import sy…”; code/src/evaluation/audit_data_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…and data/processed/ for synthetic data or placeholders. Confirm…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --step ingest; python code/main.py --step evaluate; python code/main.py --step report; 4 declared deliverable(s) absent: data/processed/skill_index.npz; data/processed/weights_flattened.npz; data/results/linearity_validation.json

## Failing / missing run-book commands

- python -c "import torch, transformers, sentence_transformers; print('All deps OK')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-887-llmxive-follow-up-extending-latentskill/lib/python3.11/site-packages/torch/__init__.py", line 496, in <module>
    from torch._C import *  # noqa: F403
    ^^^^^^^^^^^^^^^^^^^^^^
ImportError: /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-887-llmxive-follow-up-extending-latentskill/lib/python3.11/site-packages/torch/lib/libtorch_cuda.so: undefined symbol: ncclCommResume

- python code/main.py --step ingest -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-887-llmxive-follow-up-extending-latentskill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step evaluate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-887-llmxive-follow-up-extending-latentskill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step report -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-887-llmxive-follow-up-extending-latentskill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/code/main.py': [Errno 2] No such file or directory

- python code/utils/seeds.py --verify -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-887-llmxive-follow-up-extending-latentskill/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-887-llmxive-follow-up-extending-latentskill/code/utils/seeds.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/skill_index.npz
- data/processed/weights_flattened.npz
- data/results/linearity_validation.json
- data/results/stats_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/skill_index.npz` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_dummy_index.py` — NOT invoked by the run-book
    - `code/scripts/run_t014b.py` — NOT invoked by the run-book
    - `code/scripts/run_t022b.py` — NOT invoked by the run-book
    - `code/scripts/run_t078.py` — NOT invoked by the run-book
    - `code/src/evaluation/audit_data_integrity.py` — NOT invoked by the run-book
    - `code/src/evaluation/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/src/retrieval/query.py` — NOT invoked by the run-book
    - `code/src/retrieval/strategies.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/skill_index.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/weights_flattened.npz` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_t078.py` — NOT invoked by the run-book
    - `code/src/evaluation/audit_data_integrity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/weights_flattened.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/linearity_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/audit_data_integrity.py` — NOT invoked by the run-book
    - `code/src/evaluation/final_report.py` — NOT invoked by the run-book
    - `code/src/evaluation/report_generator.py` — NOT invoked by the run-book
    - `code/src/evaluation/summary_generator.py` — NOT invoked by the run-book
    - `code/src/utils/plotting.py` — NOT invoked by the run-book
    - `src/evaluation/final_report.py` — NOT invoked by the run-book
    - `src/evaluation/summary_generator.py` — NOT invoked by the run-book
    - `src/utils/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/linearity_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stats_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/audit_data_integrity.py` — NOT invoked by the run-book
    - `code/src/evaluation/final_report.py` — NOT invoked by the run-book
    - `code/src/evaluation/report_generator.py` — NOT invoked by the run-book
    - `code/src/evaluation/stats.py` — NOT invoked by the run-book
    - `code/src/evaluation/summary_generator.py` — NOT invoked by the run-book
    - `code/src/evaluation/verify_specs.py` — NOT invoked by the run-book
    - `code/src/evaluation/verify_stats_report.py` — NOT invoked by the run-book
    - `src/evaluation/final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stats_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
