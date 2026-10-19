# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic data using the utility m…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic dataset for reproducibility...")…”
- code/scripts/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…RESHOLD)         # Merge synthetic into data (simple append for now)…”
- code/scripts/ingest_zenodo.py: synthetic/fake INPUT data not authorized by the spec — “…v.aaq1566. Falls back to synthetic data generation if the primar…”
- code/scripts/ingest_zenodo.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data as a fallback when…”
- code/scripts/ingest_zenodo.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with synthetic data.     """     logger.info…”
- code/scripts/ingest_zenodo.py: synthetic/fake INPUT data not authorized by the spec — “…ng {target_rows} rows of synthetic fallback data.")     try:         df =…”
- code/scripts/ingest_zenodo.py: synthetic/fake INPUT data not authorized by the spec — “…gger.info(f"Successfully generated synthetic dataset with {len(df)} r…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 20 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic data using the utility m…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic dataset for reproducibility...")…”; code/scripts/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…RESHOLD)         # Merge synthetic into data (simple append for now)…”; 7 command(s) failed: python code/main.py --step ingest (rc=1); python code/main.py (rc=1); python code/main.py --step features (rc=1); 4 declared deliverable(s) absent: data/processed/completeness_check.json; data/processed/engineered_dataset.csv; data/processed/filtered_properties.csv

## Failing / missing run-book commands

- python code/main.py --step ingest -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/main.py", line 20, in <module>
    from utils.io import load_csv, save_csv, load_json, save_json
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/__init__.py", line 4, in <module>
    from .io import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/io.py", line 9, in <module>
    from .config import get_processed_data_path, get_raw_data_path
ImportError: cannot import name 'get_processed_data_path' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/config.py)

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/main.py", line 20, in <module>
    from utils.io import load_csv, save_csv, load_json, save_json
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/__init__.py", line 4, in <module>
    from .io import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/io.py", line 9, in <module>
    from .config import get_processed_data_path, get_raw_data_path
ImportError: cannot import name 'get_processed_data_path' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/config.py)

- python code/main.py --step features -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/main.py", line 20, in <module>
    from utils.io import load_csv, save_csv, load_json, save_json
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/__init__.py", line 4, in <module>
    from .io import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/io.py", line 9, in <module>
    from .config import get_processed_data_path, get_raw_data_path
ImportError: cannot import name 'get_processed_data_path' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/config.py)

- python code/main.py --step train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/main.py", line 20, in <module>
    from utils.io import load_csv, save_csv, load_json, save_json
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/__init__.py", line 4, in <module>
    from .io import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/io.py", line 9, in <module>
    from .config import get_processed_data_path, get_raw_data_path
ImportError: cannot import name 'get_processed_data_path' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/config.py)

- python code/main.py --step evaluate -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/main.py", line 20, in <module>
    from utils.io import load_csv, save_csv, load_json, save_json
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/__init__.py", line 4, in <module>
    from .io import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/io.py", line 9, in <module>
    from .config import get_processed_data_path, get_raw_data_path
ImportError: cannot import name 'get_processed_data_path' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/config.py)

- python -m pytest tests/unit/ -> rc=2
__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_validate_descriptors.py:15: in <module>
    from code.validate_descriptors import (
code/validate_descriptors.py:22: in <module>
    from features.descriptors import compute_all_descriptors, get_element_properties
E   ModuleNotFoundError: No module named 'features.descriptors'
=========================== short test summary info ============================
ERROR tests/unit/test_alloy_system_mapper.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_dedup.py
ERROR tests/unit/test_descriptors.py
ERROR tests/unit/test_ingest_mp.py
ERROR tests/unit/test_ingest_property_filter.py
ERROR tests/unit/test_ingest_t014.py
ERROR tests/unit/test_io.py
ERROR tests/unit/test_io_stratified_sampling.py
ERROR tests/unit/test_provenance.py
ERROR tests/unit/test_synthetic.py
ERROR tests/unit/test_t016_generation.py
ERROR tests/unit/test_train.py
ERROR tests/unit/test_training.py
ERROR tests/unit/test_validate_descriptors.py
!!!!!!!!!!!!!!!!!!! Interrupted: 15 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 15 errors in 0.92s ==============================


- python -m pytest tests/integration/ -> rc=2
-of-m/tests/integration/test_ingestion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_ingestion.py:10: in <module>
    from main import run_ingestion_pipeline, fetch_synthetic_data
code/main.py:20: in <module>
    from utils.io import load_csv, save_csv, load_json, save_json
code/utils/__init__.py:4: in <module>
    from .io import (
code/utils/io.py:9: in <module>
    from .config import get_processed_data_path, get_raw_data_path
E   ImportError: cannot import name 'get_processed_data_path' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-451-predicting-the-glass-forming-region-of-m/code/utils/config.py)
=========================== short test summary info ============================
ERROR tests/integration/test_ingest_property_filtering.py
ERROR tests/integration/test_ingestion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.30s ===============================



## Declared deliverables still missing

- data/processed/completeness_check.json
- data/processed/engineered_dataset.csv
- data/processed/filtered_properties.csv
- data/raw/synthetic_fallback.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/completeness_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/validate_completeness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/completeness_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/engineered_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_engineered_dataset.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/validate_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/engineered_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features/alloy_system_mapper.py` — NOT invoked by the run-book
    - `code/scripts/validate_completeness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_fallback.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/synthetic.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_fallback.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
