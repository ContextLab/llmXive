# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…"""Check for absence of synthetic data indicators."""         d…”
- code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…eturn False, f"Potential synthetic data indicators found: {synth…”
- code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…se, f"Error checking for synthetic data: {e}"      def _check_sc…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data. """  import os import s…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.run_all`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…"""Check for absence of synthetic data indicators."""         d…”; code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…eturn False, f"Potential synthetic data indicators found: {synth…”; code/constitutional_compliance_audit.py: synthetic/fake INPUT data not authorized by the spec — “…se, f"Error checking for synthetic data: {e}"      def _check_sc…”; 1 command(s) failed: python -m code.run_all (rc=1); 3 declared deliverable(s) absent: data/logs/label_filtering_status.json; data/models/cv_metrics.json; data/processed/processed_alloys.csv

## Failing / missing run-book commands

- python -m code.run_all -> rc=1

2026-10-23 13:37:20,428 INFO __main__: Running: /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-510-predicting-the-glass-forming-region-of-a/bin/python code/ingestion.py
2026-10-23 13:37:21,881 INFO __main__: 2026-10-23 13:37:21,553 - __main__ - INFO - === Starting ingestion pipeline ===
2026-10-23 13:37:21,553 - __main__ - INFO - Attempting to download CCR dataset from https://raw.githubusercontent.com/Materials-Data-Science-and-Informatics/Glass-Forming-Ability/master/data/experimental_ccr_dataset.csv
2026-10-23 13:37:21,639 - __main__ - ERROR - Failed to download CCR dataset: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/Materials-Data-Science-and-Informatics/Glass-Forming-Ability/master/data/experimental_ccr_dataset.csv
2026-10-23 13:37:21,639 - __main__ - CRITICAL - Aborting ingestion due to download failure.

2026-10-23 13:37:21,881 ERROR __main__: Script code/ingestion.py exited with code 1


## Declared deliverables still missing

- data/logs/label_filtering_status.json
- data/models/cv_metrics.json
- data/processed/processed_alloys.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/label_filtering_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/label_filtering_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/models/cv_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/statistical_test.py` — NOT invoked by the run-book
    - `code/train.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/cv_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — NOT invoked by the run-book
    - `code/audit_data_source.py` — NOT invoked by the run-book
    - `code/constitutional_compliance_audit.py` — NOT invoked by the run-book
    - `code/features.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/t029b_fallback.py` — NOT invoked by the run-book
    - `code/t031_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
