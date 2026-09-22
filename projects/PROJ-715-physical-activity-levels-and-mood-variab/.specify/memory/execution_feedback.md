# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/save_results.py: synthetic/fake INPUT data not authorized by the spec — “…sn't exist, as we cannot fake data.         # But wait, the…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingest.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/save_results.py: synthetic/fake INPUT data not authorized by the spec — “…sn't exist, as we cannot fake data.         # But wait, the…”; 4 command(s) failed: python code/ingest.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 3 declared deliverable(s) absent: data/processed/daily_aggregates.csv; data/processed/model_results.json; data/raw/bronze.parquet

## Failing / missing run-book commands

- python code/ingest.py -> rc=1
    ownload/5b1a9f1b9ad5a10018669804/
2026-09-22 03:51:45,601 - __main__ - WARNING - OSF download failed. Attempting HuggingFace fallback.
2026-09-22 03:51:45,601 - __main__ - INFO - Downloading from https://huggingface.co/datasets/mlfoundations/studentlife/resolve/main/studentlife_ema_steps.zip...
2026-09-22 03:51:45,755 - __main__ - ERROR - Download failed: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/mlfoundations/studentlife/resolve/main/studentlife_ema_steps.zip
2026-09-22 03:51:45,755 - __main__ - ERROR - HuggingFace download also failed.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/ingest.py", line 212, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/ingest.py", line 209, in main
    download_and_verify()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/ingest.py", line 176, in download_and_verify
    raise RuntimeError(
RuntimeError: Failed to download dataset from both OSF and HuggingFace. Cannot proceed with analysis.
- python code/preprocess.py -> rc=1
    g preprocess stats...
2026-09-22 03:51:46,292 - __main__ - ERROR - Preprocessing failed: [Errno 21] Is a directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/preprocess_stats.json'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 264, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 258, in main
    preprocess(data_source)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 226, in preprocess
    init_preprocess_stats(data_source_url)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/preprocess.py", line 86, in init_preprocess_stats
    with open(output_path, 'w') as f:
         ^^^^^^^^^^^^^^^^^^^^^^
IsADirectoryError: [Errno 21] Is a directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/preprocess_stats.json'
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/analysis.py", line 17, in <module>
    from config import get_path, set_random_seed, BOOTSTRAP_ITERATIONS, RANDOM_SEED, init_logger
ImportError: cannot import name 'RANDOM_SEED' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/config.py)
- python code/report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 73, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 70, in main
    generate_report()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 59, in generate_report
    results = load_model_results()
              ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/code/report.py", line 15, in load_model_results
    if not path.exists():
           ^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'exists'

## Declared deliverables still missing

- data/processed/daily_aggregates.csv
- data/processed/model_results.json
- data/raw/bronze.parquet

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/report.py: path = get_path('data', 'processed', 'model_results.json')
- code/report.py: path = get_path('data', 'processed', 'daily_aggregates.csv')
- code/report.py: output_path = get_path('data/processed', 'final_report.pdf')
- code/verify_raw_data.py: file_path = get_path("data", "raw", "bronze.parquet")
- code/verify_raw_data.py: state_path = get_path("state", "projects", "PROJ-715-physical-activity-levels-and-mood-variab.yaml")
- code/verify_raw_mood_std.py: input_path = get_path('data/processed', 'daily_aggregates.csv')
- code/verify_raw_mood_std.py: log_path = get_path('data/processed', 'verification.log')
- code/output_validator.py: schema_path = get_path("specs/001-physical-activity-mood-variability/contracts", "daily_aggregates.schema.yaml")
- code/output_validator.py: output_path = get_path("data/processed", "daily_aggregates.csv")
- code/save_daily_aggregates.py: input_path = get_path("data", "processed", "daily_aggregates.csv")
- code/save_daily_aggregates.py: schema_path = get_path("specs", "001-physical-activity-levels-and-mood-variab", "contracts", "daily_aggregates.schema.yaml")
- code/save_daily_aggregates.py: output_path = get_path("data", "processed", "daily_aggregates.csv")
- code/ingest.py: raw_dir = get_path("data", "raw")
- code/ingest.py: state_path = get_path("state", "projects", "PROJ-715-physical-activity-levels-and-mood-variab.yaml")
- code/save_results.py: schema_path = get_path("specs/001-physical-activity-levels-and-mood-variability/contracts/model_results.schema.yaml")
- code/save_results.py: output_path = get_path("data/processed/model_results.json")
- code/analysis.py: state_path = get_path('state', 'projects', 'PROJ-715-physical-activity-levels-and-mood-variab.yaml')
- code/analysis.py: path = get_path('data', 'processed', 'daily_aggregates.csv')
- code/analysis.py: path = get_path('data', 'processed', 'model_results.json')
- code/validate_raw.py: state_path = get_path('state', 'projects', 'PROJ-715-physical-activity-levels-and-mood-variab.yaml')
- code/validate_raw.py: parquet_path = get_path("data/raw", "bronze.parquet")
- code/preprocess.py: path = get_path("data", "raw", "bronze.parquet")
- code/preprocess.py: output_path = get_path("data", "processed", "preprocess_stats.json")
- code/preprocess.py: schema_path = get_path("specs", "001-physical-activity-levels-and-mood-variab", "contracts", "preprocess_stats.schema.yaml")
- code/preprocess.py: output_path = get_path("data", "processed", "raw_daily_aggregates.csv")

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/daily_aggregates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
    - `code/verify_raw_mood_std.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/output_validator.py` — NOT invoked by the run-book
    - `code/save_daily_aggregates.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/daily_aggregates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/save_results.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/bronze.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/verify_raw_data.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/ingest.py` — IS a run-book command
    - `code/validate_raw.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/bronze.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/daily_aggregates.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/report.py`, `code/verify_raw_mood_std.py`, `code/save_daily_aggregates.py`, `code/analysis.py`, `code/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/daily_aggregates.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/report.py`, `code/verify_raw_mood_std.py`, `code/validate_quickstart.py`, `code/output_validator.py`, `code/save_daily_aggregates.py`, `code/analysis.py`, `code/preprocess.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/model_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/report.py`, `code/save_results.py`, `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-715-physical-activity-levels-and-mood-variab/data/processed/model_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/report.py`, `code/validate_quickstart.py`, `code/save_results.py`, `code/analysis.py`.
