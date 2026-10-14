# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_golden_set_template.py: self-declared fabricated metric — “…hetic Data**: Do not generate fake scores. Your expert judgment is req…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_golden_set_template.py: self-declared fabricated metric — “…hetic Data**: Do not generate fake scores. Your expert judgment is req…”; 2 command(s) failed: python code/load_data.py --download (rc=1); python code/run_pipeline.py (rc=1); 7 declared deliverable(s) absent: data/explanation_tiers/complex_tiers.csv; data/explanation_tiers/moderate_tiers.csv; data/explanation_tiers/simple_tiers.csv

## Failing / missing run-book commands

- python code/load_data.py --download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-553-cognitive-load-optimization-adaptive-com/code/load_data.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-553-cognitive-load-optimization-adaptive-com/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-553-cognitive-load-optimization-adaptive-com/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-553-cognitive-load-optimization-adaptive-com/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/run_pipeline.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-553-cognitive-load-optimization-adaptive-com/code/run_pipeline.py", line 23, in <module>
    logging.FileHandler(PROJECT_ROOT / "logs" / "pipeline_run.log"),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-553-cognitive-load-optimization-adaptive-com/logs/pipeline_run.log'


## Declared deliverables still missing

- data/explanation_tiers/complex_tiers.csv
- data/explanation_tiers/moderate_tiers.csv
- data/explanation_tiers/simple_tiers.csv
- data/processed/golden_set.csv
- data/processed/instructional_units.csv
- data/processed/model_metrics.json
- data/simulation_results/hysteresis_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/explanation_tiers/complex_tiers.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_complex_tier.py` — NOT invoked by the run-book
    - `code/validate_and_tune_tiers.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/explanation_tiers/complex_tiers.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/explanation_tiers/moderate_tiers.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_complex_tier.py` — NOT invoked by the run-book
    - `code/generate_moderate_tier.py` — NOT invoked by the run-book
    - `code/generate_simple_tier.py` — NOT invoked by the run-book
    - `code/validate_and_tune_tiers.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/explanation_tiers/moderate_tiers.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/explanation_tiers/simple_tiers.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_simple_tier.py` — NOT invoked by the run-book
    - `code/validate_and_tune_tiers.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/explanation_tiers/simple_tiers.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/golden_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/acquire_golden_set.py` — NOT invoked by the run-book
    - `code/create_golden_set.py` — NOT invoked by the run-book
    - `code/generate_golden_set_template.py` — NOT invoked by the run-book
    - `code/load_data.py` — IS a run-book command
    - `code/run_pipeline.py` — IS a run-book command
    - `code/train_load_model.py` — NOT invoked by the run-book
    - `code/validate_and_load_golden_set.py` — NOT invoked by the run-book
    - `code/validate_golden_set.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/golden_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/instructional_units.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extract_instructional_units.py` — NOT invoked by the run-book
    - `code/generate_moderate_tier.py` — NOT invoked by the run-book
    - `code/generate_simple_tier.py` — NOT invoked by the run-book
    - `code/generate_tiers.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
    - `code/utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/instructional_units.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/train_load_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/simulation_results/hysteresis_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/hysteresis_controller.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation_results/hysteresis_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
