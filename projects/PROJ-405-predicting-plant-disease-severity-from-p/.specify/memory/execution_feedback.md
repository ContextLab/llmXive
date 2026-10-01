# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/weather_linker.py: synthetic/fake INPUT data not authorized by the spec — “…f"Aborting to prevent synthetic data fallback."     )   def _…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/weather_linker.py: synthetic/fake INPUT data not authorized by the spec — “…f"Aborting to prevent synthetic data fallback."     )   def _…”; 3 command(s) failed: python code/main.py --mode full (rc=1); python code/main.py --mode dry-run --limit 50 (rc=1); python code/main.py --stage extract_features (rc=1); 1 declared deliverable(s) absent: data/processed/unified_analysis.csv

## Failing / missing run-book commands

- python code/main.py --mode full -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/main.py", line 25, in <module>
    from utils.logging_config import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/utils/logging_config.py", line 29, in <module>
    LOG_DIR = get_path("artifacts/logs")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/config.py", line 137, in get_path
    raise KeyError(f"Path key '{path_key}' not found in config or is not a Path.")
KeyError: "Path key 'artifacts/logs' not found in config or is not a Path."
- python code/main.py --mode dry-run --limit 50 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/main.py", line 25, in <module>
    from utils.logging_config import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/utils/logging_config.py", line 29, in <module>
    LOG_DIR = get_path("artifacts/logs")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/config.py", line 137, in get_path
    raise KeyError(f"Path key '{path_key}' not found in config or is not a Path.")
KeyError: "Path key 'artifacts/logs' not found in config or is not a Path."
- python code/main.py --stage extract_features -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/main.py", line 25, in <module>
    from utils.logging_config import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/utils/logging_config.py", line 29, in <module>
    LOG_DIR = get_path("artifacts/logs")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-405-predicting-plant-disease-severity-from-p/code/config.py", line 137, in get_path
    raise KeyError(f"Path key '{path_key}' not found in config or is not a Path.")
KeyError: "Path key 'artifacts/logs' not found in config or is not a Path."

## Declared deliverables still missing

- data/processed/unified_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/unified_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
    - `code/utils/validity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `unified_analysis.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[Path key]`
- PRODUCER(s) to edit: `code/modeling.py`, `code/data_ingestion.py`, `code/visualization.py`
- CONSUMER(s) that read it: `code/modeling.py`, `code/config.py`, `code/visualization.py`, `code/utils/validity_check.py`
  → Edit the producer so every required name [Path key] is in `unified_analysis.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
