# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/extract_descriptors.py: self-declared fabricated metric — “…ion`` column (filled with the placeholder value ``Unknown``),     and write a…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/extract_descriptors.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/extract_descriptors.py: self-declared fabricated metric — “…ion`` column (filled with the placeholder value ``Unknown``),     and write a…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/train_baseline.py; python code/stat_test.py; python code/evaluate_reduced.py; 7 command(s) failed: python code/download_data.py (rc=1); python code/extract_descriptors.py (rc=1); python code/preprocess.py (rc=1); 5 declared deliverable(s) absent: data/processed/aligned_dataset.csv; data/processed/oc20_descriptors.parquet; data/processed/unified_dataset.parquet

## Failing / missing run-book commands

- python code/download_data.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/download_data.py", line 24, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.2

- python code/extract_descriptors.py -> rc=1
File "parsers.pyx", line 696, in pandas._libs.parsers.TextReader._get_header
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8b in position 1: invalid start byte

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 282, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 236, in main
    oc20_df = load_oc20_sample()
              ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 97, in load_oc20_sample
    path = _ensure_oc20_sample()
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 62, in _ensure_oc20_sample
    raise RuntimeError(
RuntimeError: Failed to download fallback CSV for OC20 sample: 'utf-8' codec can't decode byte 0x8b in position 1: invalid start byte

- python code/preprocess.py -> rc=1
k/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 47, in load_extracted_descriptors
    raise FileNotFoundError(f"Unified dataset not found at {path}")
FileNotFoundError: Unified dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/processed/unified_dataset.parquet

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 136, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 72, in main
    df = load_extracted_descriptors()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 47, in load_extracted_descriptors
    raise FileNotFoundError(f"Unified dataset not found at {path}")
FileNotFoundError: Unified dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/processed/unified_dataset.parquet

- python code/train.py          # XGBoost -> rc=1

Runtime projection file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/outputs/runtime_projection.json. Proceeding with default max_n_estimators=200.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train.py", line 220, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train.py", line 194, in main
    df = load_aligned_dataset()
         ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train.py", line 28, in load_aligned_dataset
    raise FileNotFoundError(f"Aligned dataset not found at {file_path}")
FileNotFoundError: Aligned dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/processed/aligned_dataset.csv

- python code/train_baseline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train_baseline.py': [Errno 2] No such file or directory

- python code/stat_test.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/stat_test.py': [Errno 2] No such file or directory

- python code/interpret.py -> rc=1
026-10-23 20:12:29,597 INFO __main__: ================================================================================
2026-10-23 20:12:29,597 INFO __main__: T106: SHAP Analysis and SC-003 Verification
2026-10-23 20:12:29,598 INFO __main__: ================================================================================
2026-10-23 20:12:29,598 ERROR __main__: Error in T106: Best XGBoost model not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/models/best_xgboost.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/interpret.py", line 287, in main
    model_full = load_best_xgboost_model()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/interpret.py", line 35, in load_best_xgboost_model
    raise FileNotFoundError(f"Best XGBoost model not found at {model_path}")
FileNotFoundError: Best XGBoost model not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/models/best_xgboost.json

- python code/evaluate_reduced.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/evaluate_reduced.py': [Errno 2] No such file or directory

- python code/report.py -> rc=1
3 20:12:29,876 - __main__ - ERROR - Report generation failed: Metrics file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/results/metrics.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 247, in main
    output_file = run_report_generation()
                  ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 215, in run_report_generation
    raise e
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 203, in run_report_generation
    metrics = load_metrics()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 33, in load_metrics
    raise FileNotFoundError(f"Metrics file not found at {path}")
FileNotFoundError: Metrics file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/results/metrics.json

- python -m pytest -v -> rc=2
home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py)

During handling of the above exception, another exception occurred:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_preprocess.py:17: in <module>
    from code.preprocess import (
E   ImportError: cannot import name 'normalize_composition' from 'code.preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py)
=========================== short test summary info ============================
ERROR tests/test_config.py
ERROR tests/test_download.py
ERROR tests/test_download_data.py
ERROR tests/test_generate_aligned_dataset.py
ERROR tests/test_hashing.py
ERROR tests/test_preprocess.py
ERROR tests/test_preprocess_scaling.py
ERROR tests/test_report.py
ERROR tests/unit/test_download_data.py
ERROR tests/unit/test_preprocess.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 1.43s ==============================



## Declared deliverables still missing

- data/processed/aligned_dataset.csv
- data/processed/oc20_descriptors.parquet
- data/processed/unified_dataset.parquet
- data/raw/experimental_tof.csv
- data/raw/oc20_sample.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
    - `code/generate_aligned_dataset.py` — NOT invoked by the run-book
    - `code/interpret.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/train.py` — IS a run-book command
    - `code/utils/runtime_estimator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/oc20_descriptors.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/extract_descriptors.py` — IS a run-book command
    - `code/preprocess_alignment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/oc20_descriptors.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unified_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/preprocess_alignment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/experimental_tof.csv` is declared but was NOT written. Scripts referencing it:
    - `code/acquire_tof.py` — NOT invoked by the run-book
    - `code/download_data.py` — IS a run-book command
    - `code/interpret.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/preprocess_alignment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/experimental_tof.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/oc20_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/compute_alignment_metrics.py` — NOT invoked by the run-book
    - `code/download_data.py` — IS a run-book command
    - `code/extract_descriptors.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/oc20_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
