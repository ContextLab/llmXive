# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/model_comparison.py: self-declared fabricated metric — “…ion     # For this script, we simulate the results based on the data to ensure…”
- code/analysis/model_comparison.py: self-declared fabricated metric — “…ment of the data,     # not a mock value.      # Baseline Model: Judgm…”
- code/analysis/model_comparison.py: synthetic/fake INPUT data not authorized by the spec — “…lated_data: DataFrame of simulated data from posterior.…”
- code/analysis/model_comparison.py: synthetic/fake INPUT data not authorized by the spec — “…e)      # Perform PPC if simulated data is available (simulated…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…MODE is 'simulation', it generates synthetic data. If DATA_MODE is 'r…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…Load MFQ data from the generated synthetic dataset or real source.…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating synthetic MFQ data...")         generate_mf…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…aise FileNotFoundError(f"Synthetic MFQ data not found at {data_path}…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 31 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/model_comparison.py: self-declared fabricated metric — “…ion     # For this script, we simulate the results based on the data to ensure…”; code/analysis/model_comparison.py: self-declared fabricated metric — “…ment of the data,     # not a mock value.      # Baseline Model: Judgm…”; code/analysis/model_comparison.py: synthetic/fake INPUT data not authorized by the spec — “…lated_data: DataFrame of simulated data from posterior.…”; 8 command(s) failed: python code/data/ingest.py (rc=1); python code/data/simulation.py (rc=1); python code/data/preprocess.py (rc=1)

## Failing / missing run-book commands

- python code/data/ingest.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/ingest.py", line 21, in <module>
    from utils.logging import get_logger, get_exclusion_log_path, log_exclusion, log_pipeline_step
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 22, in <module>
    from .norms import (
ImportError: cannot import name 'load_gervais_norms' from 'utils.norms' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/norms.py)
- python code/data/simulation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/simulation.py", line 32, in <module>
    from code.data.simulation_mfq import main as generate_mfq
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/simulation_mfq.py", line 28, in <module>
    from code.utils.norms import load_norms_data, get_means, get_std_devs, get_covariance_matrix
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 22, in <module>
    from .norms import (
ImportError: cannot import name 'load_gervais_norms' from 'code.utils.norms' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/norms.py)
- python code/data/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/preprocess.py", line 25, in <module>
    from utils.logging import get_logger, get_vr_mapping_log_path, log_vr_mapping
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 22, in <module>
    from .norms import (
ImportError: cannot import name 'load_gervais_norms' from 'utils.norms' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/norms.py)
- python code/models/bayesian.py -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/.venv/lib/python3.11/site-packages/arviz/__init__.py:50: FutureWarning: 
ArviZ is undergoing a major refactor to improve flexibility and extensibility while maintaining a user-friendly interface.
Some upcoming changes may be backward incompatible.
For details and migration guidance, visit: https://python.arviz.org/en/latest/user_guide/migration_guide.html
  warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian.py", line 23, in <module>
    from utils.logging_utils import get_logger, log_pipeline_step
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 22, in <module>
    from .norms import (
ImportError: cannot import name 'load_gervais_norms' from 'utils.norms' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/norms.py)
- python code/analysis/model_comparison.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/model_comparison.py", line 14, in <module>
    from utils.logging_utils import get_logger, log_pipeline_step
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 22, in <module>
    from .norms import (
ImportError: cannot import name 'load_gervais_norms' from 'utils.norms' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/norms.py)
- python code/analysis/validation.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/validation.py", line 19, in <module>
    from utils.logging_utils import get_logger, log_pipeline_step
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 22, in <module>
    from .norms import (
ImportError: cannot import name 'load_gervais_norms' from 'utils.norms' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/norms.py)
- python code/utils/hashing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/hashing.py", line 15, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/logging.py", line 25, in <module>
    def get_logger(name: str) -> logging.Logger:
                                 ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import)
- python code/reports/generate_report.py -> rc=1
    2026-07-21 03:27:11,443 - __main__ - INFO - Starting report generation...
2026-07-21 03:27:11,443 - __main__ - INFO - Running in True mode
2026-07-21 03:27:11,443 - __main__ - WARNING - Result file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/model_results.json
2026-07-21 03:27:11,443 - __main__ - ERROR - No result data found. Cannot generate report.
2026-07-21 03:27:11,444 - __main__ - INFO - Failure report written to /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/reports/final_validation_report.txt

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/config.py: 1. get_path("data/processed/output.csv") -> Returns PROJECT_ROOT / "data/processed/output.csv"
- code/config.py: 2. get_path("data", "logs/exclusion.log") -> Returns PROJECT_ROOT / "data" / "logs/exclusion.log"
- code/config.py: 3. get_path("", "data/raw/file.csv") -> Returns PROJECT_ROOT / "data/raw/file.csv"
- code/config.py: raise ValueError("get_path() requires at least one path argument")
- code/config.py: full_path = get_path(file_path)
- code/models/bayesian.py: data_path = get_path("data/processed/merged_data.csv")
- code/models/bayesian.py: output_path = get_path("data/processed/model_result.json")
- code/utils/logging.py: log_dir = get_path("data/logs")
- code/utils/logging.py: log_file = get_path("data/logs", "pipeline.log")
- code/utils/logging.py: return get_path("data/logs", filename)
- code/utils/logging.py: return get_path("data/logs", "exclusion.log")
- code/utils/logging.py: return get_path("data/logs", "vr_mapping.log")
- code/utils/norms.py: config_path = get_path(NORMS_CONFIG_PATH)
- code/utils/norms.py: config_path = get_path(config_path)
- code/utils/norms.py: output_path = get_path("data/raw/synthetic_mfq_norms_sample.csv")
- code/utils/norms.py: report_path = get_path("data/logs/norms_validation_report.json")
- code/utils/hashing.py: state_file = str(get_path("state", "pipeline_state.yaml"))
- code/utils/logging_utils.py: LOG_DIR = Path(get_path("data/logs"))
- code/reports/generate_report.py: logging.FileHandler(get_path('data/logs/report_generation.log'))
- code/reports/generate_report.py: results_path = get_path('data/processed/model_results.json')
- code/reports/generate_report.py: output_path = get_path('reports/final_validation_report.txt')
- code/data/ingest.py: data_path = get_path("data/raw/synthetic_mfq.csv")
- code/data/ingest.py: data_path = get_path("data/raw/synthetic_stories.csv")
- code/data/ingest.py: data_path = get_path("data/raw/synthetic_vr_logs.csv")
- code/data/ingest.py: output_path = get_path("data/processed/merged_data.csv")

Make `get_path` in `code/config.py` accept ALL of the above.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/model_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/utils/hashing.py`, `code/reports/generate_report.py`, `code/analysis/validation.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/model_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/utils/hashing.py`, `code/reports/generate_report.py`, `code/analysis/validation.py`.
