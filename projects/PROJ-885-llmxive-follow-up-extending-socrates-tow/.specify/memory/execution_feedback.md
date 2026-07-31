# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…Injection.  This module generates synthetic conflict dialogue trajec…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…ured, # schema-compliant synthetic data that simulates real conf…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…t, ) -> str:     """     Generates a synthetic dialogue turn based on m…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…Injection.  This module generates synthetic conflict dialogue trajec…”; code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…ured, # schema-compliant synthetic data that simulates real conf…”; code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…t, ) -> str:     """     Generates a synthetic dialogue turn based on m…”; 5 run-book script(s) missing (plan/impl path mismatch): python src/data/generate_trajectories.py --download-only; python src/data/generate_trajectories.py --oversample-high-difficulty; python src/data/classifier_training.py; 1 command(s) failed: python code/experiments/runner.py --models llama-3-8b,mistral-7b --conditions adapter,static (rc=1); 3 declared deliverable(s) absent: data/processed/classifier_training_data.json; data/processed/experiment_logs.json; data/processed/trajectories.json

## Failing / missing run-book commands

- python src/data/generate_trajectories.py --download-only -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/data/generate_trajectories.py': [Errno 2] No such file or directory
- python src/data/generate_trajectories.py --oversample-high-difficulty -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/data/generate_trajectories.py': [Errno 2] No such file or directory
- python src/data/classifier_training.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/data/classifier_training.py': [Errno 2] No such file or directory
- python code/experiments/runner.py --models llama-3-8b,mistral-7b --conditions adapter,static -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/experiments/runner.py", line 5, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python src/analysis/stats_utils.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/analysis/stats_utils.py': [Errno 2] No such file or directory
- python tests/integration/test_quickstart_validation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/tests/integration/test_quickstart_validation.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/classifier_training_data.json
- data/processed/experiment_logs.json
- data/processed/trajectories.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/classifier_training_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/classifier.py` — NOT invoked by the run-book
    - `code/analysis/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/classifier_training_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/experiment_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/evaluator.py` — NOT invoked by the run-book
    - `code/analysis/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/log_writer.py` — NOT invoked by the run-book
    - `code/analysis/perf_monitor.py` — NOT invoked by the run-book
    - `code/experiments/runner.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/experiment_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trajectories.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/models/entities.py` — NOT invoked by the run-book
    - `code/models/evaluator.py` — NOT invoked by the run-book
    - `code/analysis/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/perf_monitor.py` — NOT invoked by the run-book
    - `code/experiments/runner.py` — IS a run-book command
    - `code/data/loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trajectories.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
