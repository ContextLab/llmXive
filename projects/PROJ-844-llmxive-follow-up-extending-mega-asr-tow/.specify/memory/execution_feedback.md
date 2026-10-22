# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/human_validation.py: self-declared fabricated metric — “…generate a template     with placeholder scores (or simulate a real run if t…”
- code/human_validation.py: metric `score` assigned from an RNG draw (line 88)

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/human_validation.py: self-declared fabricated metric — “…generate a template     with placeholder scores (or simulate a real run if t…”; code/human_validation.py: metric `score` assigned from an RNG draw (line 88); 4 command(s) failed: python -m src.utils.logging verify_checksums (rc=1); python -m src.pipeline.run all  +seed=42  +sample_size=50000  +distortion_grid.snr_levels="[-12,-9,-6,-3,0,3,6,9,12]"  +distortion_grid.rt_levels="[0.2,0.4,0.6,0.8,1.0,1.2]"  +use_paid_cluster=true  +gpu_shards=4   # split into four parallel GPU nodes (rc=1); python -m pytest -v (rc=2); 3 declared deliverable(s) absent: data/derived/collapse_points.parquet; data/derived/critical_vector.parquet; data/derived/stress_curves.parquet

## Failing / missing run-book commands

- python -m src.utils.logging verify_checksums -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/bin/python: Error while finding module specification for 'src.utils.logging' (ModuleNotFoundError: No module named 'src')

- python -m src.pipeline.run all  +seed=42  +sample_size=50000  +distortion_grid.snr_levels="[-12,-9,-6,-3,0,3,6,9,12]"  +distortion_grid.rt_levels="[0.2,0.4,0.6,0.8,1.0,1.2]"  +use_paid_cluster=true  +gpu_shards=4   # split into four parallel GPU nodes -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/bin/python: Error while finding module specification for 'src.pipeline.run' (ModuleNotFoundError: No module named 'src')

- python -m pytest -v -> rc=2
importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_streaming_loader.py:12: in <module>
    from data_loader import (
E   ImportError: cannot import name 'StreamingStressCurveLoader' from 'data_loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py)
=========================== short test summary info ============================
ERROR tests/integration/test_data_loader_workflow.py
ERROR tests/test_config.py
ERROR tests/test_data_loader_coverage.py
ERROR tests/unit/test_data_loader_integration.py
ERROR tests/unit/test_data_loader_streaming.py
ERROR tests/unit/test_statistics.py
ERROR tests/unit/test_streaming_loader.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 1.41s ===============================


- python -m src.pipeline.visualize  --stress-curves data/derived/stress_curves.parquet  --collapse-points data/derived/collapse_points.parquet  --critical-vectors data/derived/critical_vector.parquet  --output-dir figures/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/bin/python: Error while finding module specification for 'src.pipeline.visualize' (ModuleNotFoundError: No module named 'src')


## Declared deliverables still missing

- data/derived/collapse_points.parquet
- data/derived/critical_vector.parquet
- data/derived/stress_curves.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/collapse_points.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/collapse_points_generator.py` — NOT invoked by the run-book
    - `code/run_quickstart.py` — NOT invoked by the run-book
    - `code/validation_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/collapse_points.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/critical_vector.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/critical_vector.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/stress_curves.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/collapse_points_generator.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/run_quickstart.py` — NOT invoked by the run-book
    - `code/validation_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/stress_curves.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
