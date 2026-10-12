# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/models.py: synthetic/fake INPUT data not authorized by the spec — “…erformance]:     """     Generate synthetic performance records for…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/models.py: synthetic/fake INPUT data not authorized by the spec — “…erformance]:     """     Generate synthetic performance records for…”; 3 command(s) failed: python code/main_pipeline.py (rc=1); python -m pytest tests/unit/test_spatial_metrics.py -v (rc=1); python -m pytest tests/integration/test_pipeline.py -v (rc=4); 4 declared deliverable(s) absent: data/processed/spatial_metrics.csv; data/processed/unified_dataset.csv; data/results/data_feasibility_report.json

## Failing / missing run-book commands

- python code/main_pipeline.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl/code/main_pipeline.py", line 20, in <module>
    from data.ingest import ingest_and_filter_dataset
ModuleNotFoundError: No module named 'data.ingest'

- python -m pytest tests/unit/test_spatial_metrics.py -v -> rc=1
oopError: ufunc 'add' did not contain a loop with signature matching types (dtype('<U8'), dtype('<U8')) -> None
FAILED tests/unit/test_spatial_metrics.py::TestComputeSpatialMetricsForSample::test_compute_metrics_with_gaussian_data - numpy.core._exceptions._UFuncNoLoopError: ufunc 'add' did not contain a loop with signature matching types (dtype('<U13'), dtype('<U13')) -> None
FAILED tests/unit/test_spatial_metrics.py::TestComputeSpatialMetricsForSample::test_compute_metrics_with_exponential_data - numpy.core._exceptions._UFuncNoLoopError: ufunc 'add' did not contain a loop with signature matching types (dtype('<U8'), dtype('<U8')) -> None
FAILED tests/unit/test_spatial_metrics.py::TestProcessDatasetAndWriteMetrics::test_process_dataset_creates_file - AssertionError: assert 'data_path' in ['dataset_path', 'output_path', 'map_columns', 'pixel_size']
FAILED tests/unit/test_spatial_metrics.py::TestProcessDatasetAndWriteMetrics::test_process_dataset_with_real_sample - Failed: process_dataset_and_write_metrics failed: process_dataset_and_write_metrics() missing 1 required positional argument: 'map_columns'
========================= 18 failed, 1 passed in 0.86s =========================


- python -m pytest tests/integration/test_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-204-quantifying-the-impact-of-spatial-correl/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-204-quantifying-the-impact-of-spatial-correl
configfile: pyproject.toml
plugins: typeguard-4.6.0, platformdirs-4.13.0
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_pipeline.py



## Declared deliverables still missing

- data/processed/spatial_metrics.csv
- data/processed/unified_dataset.csv
- data/results/data_feasibility_report.json
- data/results/ingestion_stats.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/spatial_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/spatial_metrics.py` — NOT invoked by the run-book
    - `code/main_pipeline.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/spatial_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unified_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/spatial_metrics.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/validation/co_location.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/data_feasibility_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/feasibility.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/data_feasibility_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/ingestion_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/main_pipeline.py` — IS a run-book command
    - `code/report/generate.py` — NOT invoked by the run-book
    - `code/utils/ingestion_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ingestion_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
