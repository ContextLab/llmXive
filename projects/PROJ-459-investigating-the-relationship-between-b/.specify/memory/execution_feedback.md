# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: self-declared fabricated metric — “…th)     logger.info(f"Written dummy metrics to {metrics_path}")      log…”
- code/analysis/metrics.py: synthetic/fake INPUT data not authorized by the spec — “…on entry point."""     # Generate synthetic data for illustration…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py --step download_and_validate`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: self-declared fabricated metric — “…th)     logger.info(f"Written dummy metrics to {metrics_path}")      log…”; code/analysis/metrics.py: synthetic/fake INPUT data not authorized by the spec — “…on entry point."""     # Generate synthetic data for illustration…”; 6 command(s) failed: python code/main.py --step download_and_validate (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step compute_metrics (rc=1); 1 declared deliverable(s) absent: data/derived/final_results.csv

## Failing / missing run-book commands

- python code/main.py --step download_and_validate -> rc=1
home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 258, in main
    step_download_and_validate(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 69, in step_download_and_validate
    download_dataset(ds_id, str(get_data_path()))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 154, in download_dataset
    raise exc
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 151, in download_dataset
    file_list = _list_dataset_files(dataset_id)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/download.py", line 80, in _list_dataset_files
    raise ConnectionError(f"Unable to list files for dataset {dataset_id}: {exc}") from exc
ConnectionError: Unable to list files for dataset ds000030: 404 Client Error: Not Found for url: https://openneuro.org/crn/datasets/ds000030/snapshots/latest/files

- python code/main.py --step preprocess -> rc=1

2026-10-13 09:31:47,538 - __main__ - INFO - Starting step: preprocess
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 280, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 260, in main
    step_preprocess(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 89, in step_preprocess
    validate_environment()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/utils/docker.py", line 84, in validate_environment
    raise RuntimeError("fMRIPrep Docker image not found locally.")
RuntimeError: fMRIPrep Docker image not found locally.

- python code/main.py --step compute_metrics -> rc=1

2026-10-13 09:31:50,115 - __main__ - INFO - Starting step: compute_metrics
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 280, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 262, in main
    step_compute_metrics(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 104, in step_compute_metrics
    derived_path = get_derived_path()
                   ^^^^^^^^^^^^^^^^^^
TypeError: get_derived_path() missing 1 required positional argument: 'filename'

- python code/main.py --step analyze -> rc=1

2026-10-13 09:31:50,513 - __main__ - INFO - Starting step: analyze
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 280, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 264, in main
    step_analyze(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 129, in step_analyze
    derived_path = get_derived_path()
                   ^^^^^^^^^^^^^^^^^^
TypeError: get_derived_path() missing 1 required positional argument: 'filename'

- python -m pytest tests/contract/ -> rc=2
en-b
configfile: pyproject.toml
collected 13 items / 1 error

==================================== ERRORS ====================================
____________ ERROR collecting tests/contract/test_metric_schema.py _____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/tests/contract/test_metric_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_metric_schema.py:11: in <module>
    from data.models import NetworkMetric, CorrelationResult, SensitivityReport
code/data/models.py:23: in <module>
    from pydantic import BaseModel, Field, validator
E   ModuleNotFoundError: No module named 'pydantic'
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.56s ===============================


- python -m pytest tests/unit/ -> rc=2
he-relationship-between-b/tests/unit/test_stats_null_validation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_stats_null_validation.py:4: in <module>
    from analysis.stats import run_null_distribution_validation
code/analysis/stats.py:3: in <module>
    from scipy.stats import spearmanr, power
E   ImportError: cannot import name 'power' from 'scipy.stats' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-459-investigating-the-relationship-between-b/lib/python3.11/site-packages/scipy/stats/__init__.py)
=========================== short test summary info ============================
ERROR tests/unit/test_config_io.py
ERROR tests/unit/test_io.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_sensitivity_report.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_stats_null_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 0.83s ===============================



## Declared deliverables still missing

- data/derived/final_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
