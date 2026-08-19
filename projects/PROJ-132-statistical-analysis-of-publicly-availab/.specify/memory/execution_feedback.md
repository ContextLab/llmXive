# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…irectory. To download or generate synthetic data:  ```bash python co…”
- code/benchmark_runtime.py: synthetic/fake INPUT data not authorized by the spec — “…: int = 1000000):     """Generate a large synthetic dataset for benchmarking…”
- code/benchmark_runtime.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with {n_rows} rows...")…”
- code/benchmark_runtime.py: synthetic/fake INPUT data not authorized by the spec — “…ws} rows...")          # Generate synthetic eBird data     np.random…”
- code/benchmark_runtime.py: synthetic/fake INPUT data not authorized by the spec — “…)          logger.info(f"Synthetic data generated: {ebird_file}"…”
- code/src/models/gamm_fit.py: synthetic/fake INPUT data not authorized by the spec — “…t_path} not found. Using simulated data.")          run_gamm_pip…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/README.md: synthetic/fake INPUT data not authorized by the spec — “…irectory. To download or generate synthetic data:  ```bash python co…”; code/benchmark_runtime.py: synthetic/fake INPUT data not authorized by the spec — “…: int = 1000000):     """Generate a large synthetic dataset for benchmarking…”; code/benchmark_runtime.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with {n_rows} rows...")…”; 1 command(s) failed: python code/run_pipeline.py (rc=1); 8 declared deliverable(s) absent: data/interim/trajectory_statistics.json; data/interim/weekly_centroids.parquet; data/processed/imputation_metadata.json

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-132-statistical-analysis-of-publicly-availab/code/run_pipeline.py", line 8, in <module>
    from src.data.download import run_download_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-132-statistical-analysis-of-publicly-availab/code/src/data/download.py", line 10, in <module>
    from src.config import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-132-statistical-analysis-of-publicly-availab/code/src/config.py", line 96, in <module>
    setup_logging()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-132-statistical-analysis-of-publicly-availab/code/src/config.py", line 59, in setup_logging
    file_handler = logging.handlers.RotatingFileHandler(
                   ^^^^^^^^^^^^^^^^
AttributeError: module 'logging' has no attribute 'handlers'. Did you mean: '_handlers'?

## Declared deliverables still missing

- data/interim/trajectory_statistics.json
- data/interim/weekly_centroids.parquet
- data/processed/imputation_metadata.json
- data/processed/metadata_insufficient_cells.json
- data/processed/preprocessed_data.parquet
- data/provenance/data_availability_report.json
- data/provenance/row_mapping.json
- data/raw/migratory_list.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/trajectory_statistics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/trajectory_stats.py` — NOT invoked by the run-book
    - `code/tests/unit/test_trajectory_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/trajectory_statistics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/weekly_centroids.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/trajectory_stats.py` — NOT invoked by the run-book
    - `code/src/models/trajectory.py` — NOT invoked by the run-book
    - `code/tests/unit/test_trajectory.py` — NOT invoked by the run-book
    - `code/tests/unit/test_trajectory_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/weekly_centroids.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/imputation_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_preprocess_t017b.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/imputation_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata_insufficient_cells.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_metrics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_t015b.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_t018.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata_insufficient_cells.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/preprocessed_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/gamm_fit.py` — NOT invoked by the run-book
    - `code/src/data/preprocess.py` — NOT invoked by the run-book
    - `code/tests/integration/test_preprocess_integration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/preprocessed_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/provenance/data_availability_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/verify_dataset.py` — NOT invoked by the run-book
    - `code/tests/unit/test_verify_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/provenance/data_availability_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/provenance/row_mapping.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_t016.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_provenance.py` — NOT invoked by the run-book
    - `code/tests/unit/test_provenance.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_t015b.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/provenance/row_mapping.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/migratory_list.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/preprocess.py` — NOT invoked by the run-book
    - `code/src/data/download.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/unit/test_download.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_t015b.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/migratory_list.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
