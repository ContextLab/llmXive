# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…range(n_iter):         # Generate synthetic data from fitted distrib…”
- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…lculate KS statistic for synthetic data         synth_cdf = np.s…”
- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…range(n_sim):         # Generate synthetic Log-Normal data…”
- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…range(n_boot):         # Generate synthetic data         synth_data…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_loader.py --year 2022 --save data/raw/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…range(n_iter):         # Generate synthetic data from fitted distrib…”; code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…lculate KS statistic for synthetic data         synth_cdf = np.s…”; code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…range(n_sim):         # Generate synthetic Log-Normal data…”; 3 command(s) failed: python code/main.py --year 2022 --output data/results/ (rc=1); python code/data_loader.py --year 2022 --save data/raw/ (rc=1); python code/preprocessing.py --input data/raw/bts_2022.csv --output data/processed/cleaned_delays.csv (rc=1); 2 declared deliverable(s) absent: data/results/component_comparison.json; data/results/tail_ks.json

## Failing / missing run-book commands

- python code/main.py --year 2022 --output data/results/ -> rc=1
    2026-07-17 11:34:19,957 - pipeline - INFO - Starting Flight Delay Analysis Pipeline
2026-07-17 11:34:19,957 - pipeline - INFO - Executing Stage 1: Data Acquisition and Pre-processing
2026-07-17 11:34:19,957 - pipeline - WARNING - Raw data not found at data/raw/flight_delays.csv. Attempting download...
2026-07-17 11:34:20,016 - pipeline - ERROR - Pipeline failed with error: download_bts_data() missing 1 required positional argument: 'year'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/main.py", line 158, in main
    run_stage1()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/preprocessing.py", line 168, in main
    download_bts_data()
TypeError: download_bts_data() missing 1 required positional argument: 'year'
- python code/data_loader.py --year 2022 --save data/raw/ -> rc=1
    ipeline - INFO - Attempting download (attempt 5/5): https://transtats.bts.gov/OTD/2023_OTD.csv
2026-07-17 11:35:36,959 - pipeline - WARNING - Download attempt 5 failed: 404 Client Error: Not Found for url: https://transtats.bts.gov/OTD/2023_OTD.csv
2026-07-17 11:35:36,959 - pipeline - ERROR - All 5 download attempts failed.
2026-07-17 11:35:36,960 - pipeline - ERROR - Pipeline error: Failed to download BTS data for year 2023 after 5 attempts.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/data_loader.py", line 165, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/data_loader.py", line 152, in main
    output_path = download_bts_data(year)
                  ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/data_loader.py", line 128, in download_bts_data
    raise PipelineError(f"Failed to download BTS data for year {year} after {MAX_RETRIES} attempts.")
utils.PipelineError: Failed to download BTS data for year 2023 after 5 attempts.
- python code/preprocessing.py --input data/raw/bts_2022.csv --output data/processed/cleaned_delays.csv -> rc=1
    2026-07-17 11:35:37,251 - pipeline - WARNING - Raw data not found at data/raw/flight_delays.csv. Attempting download...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/preprocessing.py", line 203, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-105-statistical-analysis-of-publicly-availab/code/preprocessing.py", line 168, in main
    download_bts_data()
TypeError: download_bts_data() missing 1 required positional argument: 'year'

## Declared deliverables still missing

- data/results/component_comparison.json
- data/results/tail_ks.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `download_bts_data` — defined in `code/data_loader.py`; called 2 way(s):

- code/data_loader.py: output_path = download_bts_data(year)
- code/preprocessing.py: download_bts_data()

Make `download_bts_data` in `code/data_loader.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/component_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/models.py` — IS a run-book command
  Make ONE of these WRITE `data/results/component_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/tail_ks.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/diagnostics.py` — IS a run-book command
  Make ONE of these WRITE `data/results/tail_ks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
