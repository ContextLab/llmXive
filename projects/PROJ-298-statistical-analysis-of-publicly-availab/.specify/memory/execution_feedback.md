# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/setup_data_structure.py: self-declared fabricated metric — “…s is REAL data structure, not fake values)     # Source: https://surve…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/setup_data_structure.py: self-declared fabricated metric — “…s is REAL data structure, not fake values)     # Source: https://surve…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python code/data/download.py (rc=1); 9 declared deliverable(s) absent: data/processed/cluster_alignment.json; data/processed/cluster_results.json; data/processed/confidence_interval.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    flow-tags/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-08-14 16:56:29,172 - __main__ - WARNING - HF dataset load failed: Dataset 'stack-exchange/stackoverflow-tags' doesn't exist on the Hub or cannot be accessed.
2026-08-14 16:56:29,172 - __main__ - INFO - Attempting direct HTTP fetch from Stack Overflow archive...
2026-08-14 16:56:29,172 - __main__ - INFO - Checking reachability of: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z
2026-08-14 16:56:31,539 - __main__ - WARNING - URL returned non-200 status: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z (Status: 404)
2026-08-14 16:56:31,540 - __main__ - ERROR - Error during processing: Primary Stack Overflow dump URL unreachable: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z. HF fallback also failed or unavailable. Cannot proceed.
2026-08-14 16:56:31,541 - __main__ - INFO - Removed empty output file.
2026-08-14 16:56:31,541 - __main__ - ERROR - === Download Failed: Primary Stack Overflow dump URL unreachable: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z. HF fallback also failed or unavailable. Cannot proceed. ===
- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-298-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-298-statistical-analysis-of-publicly-availab/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/cluster_alignment.json
- data/processed/cluster_results.json
- data/processed/confidence_interval.json
- data/processed/correlation_results.json
- data/processed/decomposition_intermediate.json
- data/processed/decomposition_results.json
- data/processed/external_metrics.json
- data/processed/trend_intermediate.json
- data/processed/trend_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cluster_alignment.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_cluster_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_alignment.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cluster_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_cluster_results.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/confidence_interval.json` is declared but was NOT written. Scripts referencing it:
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/confidence_interval.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/decomposition_intermediate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_decomposition_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/decomposition_intermediate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/decomposition_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/analysis/generate_decomposition_results.py` — NOT invoked by the run-book
    - `code/analysis/decomposition.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/decomposition_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/mapping.py` — NOT invoked by the run-book
    - `code/data/external.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trend_intermediate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/trends.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trend_intermediate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trend_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
    - `code/data/external.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trend_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
