# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ableError to fallback to mock data. """  import os import r…”
- code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…or("VERIFICATION FAILED: Synthetic data patterns found in ingest…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ableError to fallback to mock data. """  import os import r…”; code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…or("VERIFICATION FAILED: Synthetic data patterns found in ingest…”; 4 command(s) failed: python code/ingest.py --verify-only (rc=1); python code/ingest.py &&  python code/descriptors.py &&  python code/train.py &&  python code/analyze.py &&  python code/report.py (rc=1); python -m pytest tests/unit/ (rc=2); 3 declared deliverable(s) absent: data/processed/cleaned_mg.csv; data/processed/correlation_matrix.csv; data/processed/vif_diagnostic_log.json

## Failing / missing run-book commands

- python code/ingest.py --verify-only -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/ingest.py", line 195, in <module>
    @resource_monitor(runtime_limit_h=2.0, memory_limit_gb=7.0)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/contextlib.py", line 301, in helper
    return _GeneratorContextManager(func, args, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/contextlib.py", line 105, in __init__
    self.gen = func(*args, **kwds)
               ^^^^^^^^^^^^^^^^^^^
TypeError: resource_monitor() got an unexpected keyword argument 'runtime_limit_h'

- python code/ingest.py &&  python code/descriptors.py &&  python code/train.py &&  python code/analyze.py &&  python code/report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/ingest.py", line 195, in <module>
    @resource_monitor(runtime_limit_h=2.0, memory_limit_gb=7.0)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/contextlib.py", line 301, in helper
    return _GeneratorContextManager(func, args, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/contextlib.py", line 105, in __init__
    self.gen = func(*args, **kwds)
               ^^^^^^^^^^^^^^^^^^^
TypeError: resource_monitor() got an unexpected keyword argument 'runtime_limit_h'

- python -m pytest tests/unit/ -> rc=2
ode/zenodo_client.py)
=========================== short test summary info ============================
ERROR tests/unit/test_analyze.py
ERROR tests/unit/test_descriptors.py - TypeError: resource_monitor() got an u...
ERROR tests/unit/test_descriptors_io.py - TypeError: resource_monitor() got a...
ERROR tests/unit/test_ingest.py - TypeError: resource_monitor() got an unexpe...
ERROR tests/unit/test_ingest_retention.py - TypeError: resource_monitor() got...
ERROR tests/unit/test_ingest_stats.py - TypeError: resource_monitor() got an ...
ERROR tests/unit/test_ingest_t014.py - TypeError: resource_monitor() got an u...
ERROR tests/unit/test_train_artifacts.py - TypeError: resource_monitor() got ...
ERROR tests/unit/test_train_lofo.py - TypeError: resource_monitor() got an un...
ERROR tests/unit/test_train_model.py - TypeError: resource_monitor() got an u...
ERROR tests/unit/test_train_stratification.py - TypeError: resource_monitor()...
ERROR tests/unit/test_verify_resource_compliance.py
ERROR tests/unit/test_zenodo_client.py
!!!!!!!!!!!!!!!!!!! Interrupted: 13 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 13 errors in 1.33s ==============================


- python -m pytest tests/integration/ -> rc=2
_________
tests/integration/test_train_pipeline.py:19: in <module>
    from code.train import main
code/train.py:17: in <module>
    from descriptors import get_project_root, setup_logging as setup_desc_logging
code/descriptors.py:231: in <module>
    @resource_monitor(runtime_limit_h=2.0, memory_limit_gb=7.0)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/contextlib.py:301: in helper
    return _GeneratorContextManager(func, args, kwds)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/contextlib.py:105: in __init__
    self.gen = func(*args, **kwds)
E   TypeError: resource_monitor() got an unexpected keyword argument 'runtime_limit_h'
=========================== short test summary info ============================
ERROR tests/integration/test_data_ingestion.py - TypeError: resource_monitor(...
ERROR tests/integration/test_statistical_validation.py
ERROR tests/integration/test_train_cv.py - TypeError: resource_monitor() got ...
ERROR tests/integration/test_train_pipeline.py - TypeError: resource_monitor(...
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.96s ===============================



## Declared deliverables still missing

- data/processed/cleaned_mg.csv
- data/processed/correlation_matrix.csv
- data/processed/vif_diagnostic_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_mg.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/descriptors.py` — IS a run-book command
    - `code/ingest.py` — IS a run-book command
    - `code/run_full_pipeline.py` — NOT invoked by the run-book
    - `code/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_mg.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
    - `code/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_diagnostic_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/verify_t083_compliance.py` — NOT invoked by the run-book
    - `code/verify_vif_task.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_diagnostic_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
