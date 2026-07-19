# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…}          # Check if synthetic data was used as fallback…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…are provided, we cannot generate valid synthetic data.     # We will atte…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…rquet')     logger.info("Synthetic data saved to data/raw/sapt.p…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…}          # Check if synthetic data was used as fallback…”; code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…are provided, we cannot generate valid synthetic data.     # We will atte…”; code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…rquet')     logger.info("Synthetic data saved to data/raw/sapt.p…”; 3 command(s) failed: python code/data_ingestion.py (rc=1); python code/model_training.py (rc=1); python code/analysis.py (rc=1); 5 declared deliverable(s) absent: data/processed/train.parquet; data/processed/unified_dataset.parquet; data/raw/il_structures.json

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-225-predicting-molecular-interactions-in-ion/code/data_ingestion.py", line 11, in <module>
    from .config import DataIngestionError
ImportError: attempted relative import with no known parent package
- python code/model_training.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-225-predicting-molecular-interactions-in-ion/code/model_training.py", line 9, in <module>
    from .config import ModelTrainingError, load_config
ImportError: attempted relative import with no known parent package
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-225-predicting-molecular-interactions-in-ion/code/analysis.py", line 5, in <module>
    from .config import AnalysisError
ImportError: attempted relative import with no known parent package

## Declared deliverables still missing

- data/processed/train.parquet
- data/processed/unified_dataset.parquet
- data/raw/il_structures.json
- data/raw/sapt.parquet
- data/raw/spice.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/train.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/model_training.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/train.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unified_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/unified_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/il_structures.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/il_structures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sapt.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/utils.py` — NOT invoked by the run-book
    - `code/model_training.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/sapt.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/spice.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/spice.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
