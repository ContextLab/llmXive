# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ir: Directory containing synthetic data files. Defaults to data/…”
- code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading synthetic data from {data_dir}")…”
- code/save_model_results.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Loading synthetic data...")     try:         ra…”
- code/save_model_results.py: synthetic/fake INPUT data not authorized by the spec — “…r.error(f"Failed to load synthetic data: {e}")         raise…”
- code/save_model_results.py: synthetic/fake INPUT data not authorized by the spec — “…tual column names in the synthetic data     # For safety, we ins…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…nerate a single chunk of synthetic data.     This function ensur…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Starting synthetic data generation for {TOTAL_CE…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main entry point for synthetic data generation."""     loggi…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/synthetic_data_chunk_000000_002000.parquet, data/raw/synthetic_data_chunk_002000_004000.parquet, data/raw/synthetic_data_chunk_004000_006000.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ir: Directory containing synthetic data files. Defaults to data/…”; code/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading synthetic data from {data_dir}")…”; code/save_model_results.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Loading synthetic data...")     try:         ra…”; every produced artifact is gitignored (data/raw/synthetic_data_chunk_000000_002000.parquet, data/raw/synthetic_data_chunk_002000_004000.parquet, data/raw/synthetic_data_chunk_004000_006000.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 5 declared deliverable(s) absent: data/processed/exclusion_log.csv; data/processed/harmonized.parquet; data/processed/model_results.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-304-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-304-statistical-analysis-of-publicly-availab/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/exclusion_log.csv
- data/processed/harmonized.parquet
- data/processed/model_results.json
- data/processed/sc_validation_report.json
- data/processed/validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/harmonized.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/harmonize_and_save.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/harmonized.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/fdr_correction.py` — NOT invoked by the run-book
    - `code/model_selection.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/validation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sc_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
    - `code/validation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sc_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
    - `code/validation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
