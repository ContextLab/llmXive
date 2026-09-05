# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/mock_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…a fallback mechanism to generate deterministic synthetic task traces and success…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_loader.py --download --dataset alfworld/alfworld`
- `python code/data_loader.py --verify`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/mock_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…a fallback mechanism to generate deterministic synthetic task traces and success…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/main.py --config config/default.yaml; python code/main.py --granularity fine --predicates spatial+temporal; 3 command(s) failed: python code/data_loader.py --download --dataset alfworld/alfworld (rc=1); python code/data_loader.py --verify (rc=1); python code/experiment_runner.py --mode baseline-only (rc=1); 3 declared deliverable(s) absent: data/results/error_coverage.json; data/results/latency_violations.json; data/results/sweep_metrics.csv

## Failing / missing run-book commands

- python code/data_loader.py --download --dataset alfworld/alfworld -> rc=1
    Starting ALFWorld data stream (Split: train, Max: 500)...
WARNING: Remote dataset fetch failed: Dataset 'alfworld/alfworld' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.
FATAL ERROR: Remote download failed AND local fallback artifact not found at 'data/raw/alfworld_traces_train.jsonl'. Please ensure the dataset is downloaded manually or network connectivity is restored.
- python code/data_loader.py --verify -> rc=1
    Starting ALFWorld data stream (Split: train, Max: 500)...
WARNING: Remote dataset fetch failed: Dataset 'alfworld/alfworld' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.
FATAL ERROR: Remote download failed AND local fallback artifact not found at 'data/raw/alfworld_traces_train.jsonl'. Please ensure the dataset is downloaded manually or network connectivity is restored.
- python code/main.py --config config/default.yaml -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/main.py': [Errno 2] No such file or directory
- python code/main.py --granularity fine --predicates spatial+temporal -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/main.py': [Errno 2] No such file or directory
- python code/experiment_runner.py --mode baseline-only -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/experiment_runner.py", line 20, in <module>
    from graph_builder import SymbolicGraphBuilder, save_graph
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/graph_builder.py", line 16, in <module>
    from tokenizer import SymbolicTokenizer, discretize_trace
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/tokenizer.py", line 12, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

## Declared deliverables still missing

- data/results/error_coverage.json
- data/results/latency_violations.json
- data/results/sweep_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/error_coverage.json` is declared but was NOT written. Scripts referencing it:
    - `code/error_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/error_coverage.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/latency_violations.json` is declared but was NOT written. Scripts referencing it:
    - `code/latency_guard.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/latency_violations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sweep_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sweep_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
