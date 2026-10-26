# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”
- code/statistical_analysis.py: self-declared fabricated metric — “…rics CSV is empty – producing placeholder results.")     # Metrics we care abo…”
- code/data_extraction.py: synthetic/fake INPUT data not authorized by the spec — “…nting silent fallback to synthetic data. """ from __future__ imp…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.run_pipeline --full`
  - script usage: `run_pipeline.py [-h] [--csv CSV] [--out OUT] [--repos REPOS]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --full`
- run-book command: `python -m src.run_pipeline --full --samples 500`
  - script usage: `run_pipeline.py [-h] [--csv CSV] [--out OUT] [--repos REPOS]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --full --samples 500`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/power_analysis.py: self-declared fabricated metric — “…les, 3))      # Construct the simulated scores matrix:     #   mean + sqrt(…”; code/statistical_analysis.py: self-declared fabricated metric — “…rics CSV is empty – producing placeholder results.")     # Metrics we care abo…”; code/data_extraction.py: synthetic/fake INPUT data not authorized by the spec — “…nting silent fallback to synthetic data. """ from __future__ imp…”; 4 command(s) failed: python -m src.run_pipeline --sample 5 (rc=1); python -m src.run_pipeline --full (rc=2); python -m pytest tests/unit/ (rc=2)

## Failing / missing run-book commands

- python -m src.run_pipeline --sample 5 -> rc=1
4-evaluating-the-use-of-llms-for-automated/code/run_pipeline.py", line 124, in main
    rows = extract_commit_pairs(target=args.sample)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 138, in extract_commit_pairs
    commits = _fetch_commits(owner, repo, since)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 105, in _fetch_commits
    resp = _github_get(url, token)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 92, in _github_get
    resp.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 403 Client Error: rate limit exceeded for url: https://api.github.com/repos/psf/requests/commits?since=2024-10-26T13:23:35.242574Z&per_page=100&page=1

- python -m src.run_pipeline --full -> rc=2
Power analysis: estimated power for n=500 is 1.0000; exploratory=False
Wrote /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/results/power_report.md

2026-10-26 13:24:01,656 INFO code.power_analysis: Power analysis complete: power=1.0000 (n=500), exploratory=False
2026-10-26 13:24:01,656 ERROR code.data_extraction: GITHUB_TOKEN environment variable is required for data extraction
2026-10-26 13:24:01,656 ERROR code.data_extraction: Data extraction failed
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 221, in main
    raise RuntimeError("Missing GITHUB_TOKEN")
RuntimeError: Missing GITHUB_TOKEN
2026-10-26 13:24:01,665 INFO code.generation: Wrote generation success rates to /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/generated/generation_success_rates.csv
usage: run_pipeline.py [-h] [--csv CSV] [--out OUT] [--repos REPOS]
run_pipeline.py: error: unrecognized arguments: --full

- python -m pytest tests/unit/ -> rc=2
-evaluating-the-use-of-llms-for-automated/tests/unit/test_entity_extraction_intent.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/tests/unit/test_entity_extraction_intent.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_entity_extraction_intent.py:21: in <module>
    from code.entity_extraction_intent import run_extraction, DEFAULT_OUTPUT_DIR, DEFAULT_CSV, DEFAULT_REPOS_ROOT
E   ImportError: cannot import name 'DEFAULT_OUTPUT_DIR' from 'code.entity_extraction_intent' (/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/entity_extraction_intent.py)
=========================== short test summary info ============================
ERROR tests/unit/test_entity_extraction_intent.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.30s ===============================


- python -m src.run_pipeline --full --samples 500 -> rc=2
Power analysis: estimated power for n=500 is 1.0000; exploratory=False
Wrote /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/results/power_report.md

2026-10-26 13:24:15,747 INFO code.power_analysis: Power analysis complete: power=1.0000 (n=500), exploratory=False
2026-10-26 13:24:15,748 ERROR code.data_extraction: GITHUB_TOKEN environment variable is required for data extraction
2026-10-26 13:24:15,748 ERROR code.data_extraction: Data extraction failed
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/code/data_extraction.py", line 221, in main
    raise RuntimeError("Missing GITHUB_TOKEN")
RuntimeError: Missing GITHUB_TOKEN
2026-10-26 13:24:15,756 INFO code.generation: Wrote generation success rates to /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/generated/generation_success_rates.csv
usage: run_pipeline.py [-h] [--csv CSV] [--out OUT] [--repos REPOS]
run_pipeline.py: error: unrecognized arguments: --full --samples 500

## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
