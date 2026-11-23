# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/model_report.py: self-declared fabricated metric — “…observed metrics found. Using placeholder values.")         observed_metrics…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/results/partial_corr.json: EVERY metric is null/NaN (p_value, r_value) — nothing was computed

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/model_report.py: self-declared fabricated metric — “…observed metrics found. Using placeholder values.")         observed_metrics…”; 1 hollow-result signal(s) — the analysis ran but computed nothing: data/results/partial_corr.json: EVERY metric is null/NaN (p_value, r_value) — nothing was computed; 4 command(s) failed: python code/ingestion.py (rc=1); python code/modeling.py --data data/processed/cleaned_data.csv (rc=1); python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_data.csv; data/processed/residuals.csv

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1

2026-10-21 21:22:31,205 INFO __main__: Starting ingestion pipeline...
2026-10-21 21:22:31,205 ERROR __main__: Ingestion failed: Raw merged CSV not found. Please run the HCP download step (T009) to create 'data/raw/raw_merged.csv' before ingestion.

- python code/modeling.py --data data/processed/cleaned_data.csv -> rc=1

2026-10-21 21:22:31,947 INFO __main__: Loading cleaned data from data/processed/cleaned_data.csv
2026-10-21 21:22:31,947 ERROR __main__: Cleaned data file not found: data/processed/cleaned_data.csv

- python code/main.py -> rc=1

2026-10-21 21:22:33,258 INFO main: === Starting Resting‑State fMRI Global Signal Pipeline ===
2026-10-21 21:22:33,258 INFO main: Project directories verified/created.
2026-10-21 21:22:33,258 INFO main: Step 1/6: Data ingestion
2026-10-21 21:22:33,259 INFO run_ingestion_pipeline: Starting ingestion pipeline execution for T016.
2026-10-21 21:22:33,259 INFO run_ingestion_pipeline: Simulating data flow from T009-T015...
2026-10-21 21:22:33,260 INFO run_ingestion_pipeline: Motion exclusion: 0 subjects excluded.
2026-10-21 21:22:33,260 INFO run_ingestion_pipeline: Zero-variance exclusion: 0 subjects excluded.
2026-10-21 21:22:33,260 INFO run_ingestion_pipeline: Executing T016: Generating cleaned_data.csv...
2026-10-21 21:22:33,260 ERROR main: ❌ Ingestion failed: generate_cleaned_data() takes 0 positional arguments but 2 were given

- python -m pytest tests/ -v -> rc=2
lobal-signal-as-a-ma/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:89
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-723-resting-state-fmri-global-signal-as-a-ma/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../.llmxive-venvs/PROJ-723-resting-state-fmri-global-signal-as-a-ma/lib/python3.11/site-packages/matplotlib/_mathtext.py:45
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-723-resting-state-fmri-global-signal-as-a-ma/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_ingestion.py
ERROR tests/test_integration.py
ERROR tests/test_utils.py
ERROR tests/test_verify_success_criteria.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 14 warnings, 4 errors in 1.07s ========================



## Declared deliverables still missing

- data/processed/cleaned_data.csv
- data/processed/residuals.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
    - `code/modeling.py` — IS a run-book command
    - `code/robustness.py` — IS a run-book command
    - `code/run_cleaned_data_generation.py` — NOT invoked by the run-book
    - `code/run_ingestion_pipeline.py` — NOT invoked by the run-book
    - `code/run_integration_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/residuals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/modeling.py` — IS a run-book command
    - `code/robustness.py` — IS a run-book command
    - `code/setup_processed_dir.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/residuals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
