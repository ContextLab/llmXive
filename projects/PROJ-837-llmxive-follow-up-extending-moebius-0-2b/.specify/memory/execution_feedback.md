# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/training/train_gating.py: self-declared fabricated metric — “…uction weight to 0.0 or use a dummy value if not available.…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/training/train_gating.py: self-declared fabricated metric — “…uction weight to 0.0 or use a dummy value if not available.…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/data/download.py; python code/eval/evaluate.py; 4 command(s) failed: python code/data/mask_generator.py --seed <random_seed> (rc=1); python code/data/annotator.py --participants --seed 42 (rc=1); python code/training/train_gating.py --epochs [REDACTED] (rc=1); 6 declared deliverable(s) absent: data/annotations/decoupled_scores.csv; data/annotations/human_scores.csv; data/results/ablation_report.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/data/download.py': [Errno 2] No such file or directory
- python code/data/mask_generator.py --seed <random_seed> -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/data/mask_generator.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/data/annotator.py --participants --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/data/annotator.py", line 9, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/training/train_gating.py --epochs [REDACTED] -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/training/train_gating.py", line 24, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/training/train_end_to_end.py --epochs [a sufficient number of] -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/training/train_end_to_end.py", line 31, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/eval/evaluate.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/eval/evaluate.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/annotations/decoupled_scores.csv
- data/annotations/human_scores.csv
- data/results/ablation_report.json
- data/results/latency_raw.csv
- data/results/permutation_test.json
- data/results/proxy_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/annotations/decoupled_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/training/train_end_to_end.py` — IS a run-book command
    - `code/training/train_gating.py` — IS a run-book command
    - `code/data/persistor.py` — NOT invoked by the run-book
    - `code/data/annotator.py` — IS a run-book command
    - `code/data/validate_and_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/decoupled_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/annotations/human_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/training/train_end_to_end.py` — IS a run-book command
    - `code/training/train_gating.py` — IS a run-book command
    - `code/data/persistor.py` — NOT invoked by the run-book
    - `code/data/annotator.py` — IS a run-book command
    - `code/data/validate_and_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/human_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/ablation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/ablation_overhead.py` — NOT invoked by the run-book
    - `code/eval/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ablation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/latency_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/ablation_overhead.py` — NOT invoked by the run-book
    - `code/eval/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/latency_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_test.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_test.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/proxy_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/proxy_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
