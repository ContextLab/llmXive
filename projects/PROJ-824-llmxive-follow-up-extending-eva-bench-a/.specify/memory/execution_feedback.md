# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/processing/pipeline_runner.py: synthetic/fake INPUT data not authorized by the spec — “…we return deterministic mock data based on the file path…”
- code/synthetic/tts_engine.py: synthetic/fake INPUT data not authorized by the spec — “…Wrapper for Coqui TTS to generate synthetic speech with known charac…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/processing/pipeline_runner.py: synthetic/fake INPUT data not authorized by the spec — “…we return deterministic mock data based on the file path…”; code/synthetic/tts_engine.py: synthetic/fake INPUT data not authorized by the spec — “…Wrapper for Coqui TTS to generate synthetic speech with known charac…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/scripts/validate_schemas.py --input data/raw/ --schema contracts/dataset.schema.yaml; python code/analysis/comparison.py; python code/visualization/plots.py --output results/final_report.pdf; 2 command(s) failed: python code/data/download.py (rc=2); python code/tests/test_stats_models.py (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=2

2026-10-14 10:46:07,200 - llmxive.download - INFO - Starting EVA-Bench dataset download process.
2026-10-14 10:46:07,201 - llmxive.download - INFO - Downloading eva_bench_dataset.zip from https://huggingface.co/datasets/amazon-science/EVA-Bench/resolve/main/eva_bench_dataset.zip...
Download attempt 1 failed: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/amazon-science/EVA-Bench/resolve/main/eva_bench_dataset.zip
2026-10-14 10:46:07,372 - llmxive.download - CRITICAL - DOWNLOAD FAILED: Failed to download data after 0 attempts: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/amazon-science/EVA-Bench/resolve/main/eva_bench_dataset.zip
2026-10-14 10:46:07,372 - llmxive.download - CRITICAL - No fallback data source is permitted. Aborting with a non-zero exit status (task T004 fail-fast requirement).

- python code/scripts/validate_schemas.py --input data/raw/ --schema contracts/dataset.schema.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-824-llmxive-follow-up-extending-eva-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/scripts/validate_schemas.py': [Errno 2] No such file or directory

- python code/tests/test_stats_models.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_stats_models.py", line 19, in <module>
    from analysis.piecewise_regression import fit_piecewise_linear
ModuleNotFoundError: No module named 'analysis.piecewise_regression'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_stats_models.py", line 24, in <module>
    pytest.skip("analysis.piecewise_regression module not found", allow_module_level=True)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-824-llmxive-follow-up-extending-eva-bench-a/lib/python3.11/site-packages/_pytest/outcomes.py", line 179, in skip
    raise Skipped(msg=reason, allow_module_level=allow_module_level)
Skipped: analysis.piecewise_regression module not found

- python code/analysis/comparison.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-824-llmxive-follow-up-extending-eva-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/analysis/comparison.py': [Errno 2] No such file or directory

- python code/visualization/plots.py --output results/final_report.pdf -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-824-llmxive-follow-up-extending-eva-bench-a/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/visualization/plots.py': [Errno 2] No such file or directory

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
