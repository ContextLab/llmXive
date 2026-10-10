# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic subset for local testing…”
- code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…"Download CHERRL logs or generate a synthetic test subset."     )…”
- code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…ore_true",         help="Generate a deterministic synthetic subset instead of downlo…”
- code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…l‑test mode – generating synthetic data.")         df = generate…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_cherrl_logs.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic subset for local testing…”; code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…"Download CHERRL logs or generate a synthetic test subset."     )…”; code/download_cherrl_logs.py: synthetic/fake INPUT data not authorized by the spec — “…ore_true",         help="Generate a deterministic synthetic subset instead of downlo…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/compute_divergence.py; python code/detect_hacking.py; python code/evaluate.py; 2 command(s) failed: python code/download_cherrl_logs.py (rc=2); python -m pytest tests/ -v (rc=2); 4 declared deliverable(s) absent: data/processed/independence_check_status.json; data/processed/sensitivity_analysis.csv; data/processed/trajectories_divergence.csv

## Failing / missing run-book commands

- python code/download_cherrl_logs.py -> rc=2

2026-10-10 14:18:59 INFO __main__: Attempting to download CHERRL dataset 'cherrl/cherrl-logs' from HuggingFace.
2026-10-10 14:18:59 INFO httpx2: HTTP Request: GET https://huggingface.co/api/agent-harnesses "HTTP/1.1 200 OK"
2026-10-10 14:19:00 INFO httpx2: HTTP Request: HEAD https://huggingface.co/datasets/cherrl/cherrl-logs/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-10 14:19:00 ERROR __main__: Failed to connect to HuggingFace dataset cherrl/cherrl-logs: Dataset 'cherrl/cherrl-logs' doesn't exist on the Hub or cannot be accessed.
2026-10-10 14:19:00 ERROR __main__: Download failed with exit code 2

- python code/compute_divergence.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/compute_divergence.py': [Errno 2] No such file or directory

- python code/detect_hacking.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/detect_hacking.py': [Errno 2] No such file or directory

- python code/evaluate.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/evaluate.py': [Errno 2] No such file or directory

- python code/benchmark_runtime.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/benchmark_runtime.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
ruth.py)
_________________ ERROR collecting tests/unit/test_detector.py _________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/tests/unit/test_detector.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_detector.py:10: in <module>
    from detector import (
E   ImportError: cannot import name 'calculate_sliding_zscore' from 'detector' (/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-reproducing/code/detector.py)
=========================== short test summary info ============================
ERROR tests/integration/test_detector_pipeline.py
ERROR tests/integration/test_evaluation_pipeline.py
ERROR tests/unit/test_detector.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.83s ===============================



## Declared deliverables still missing

- data/processed/independence_check_status.json
- data/processed/sensitivity_analysis.csv
- data/processed/trajectories_divergence.csv
- data/processed/trajectories_labeled.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/independence_check_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/independence_check_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trajectories_divergence.csv` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_trajectories.py` — NOT invoked by the run-book
    - `code/apply_contaminated_mask.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/detector.py` — NOT invoked by the run-book
    - `code/generate_contaminated_mask.py` — NOT invoked by the run-book
    - `code/generate_labeled_trajectories.py` — NOT invoked by the run-book
    - `code/ground_truth.py` — NOT invoked by the run-book
    - `code/identify_contaminated_windows.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trajectories_divergence.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trajectories_labeled.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/evaluation.py` — NOT invoked by the run-book
    - `code/generate_labeled_trajectories.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trajectories_labeled.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
