# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ableError to fallback to mock data. """  import os import r…”
- code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…or("VERIFICATION FAILED: Synthetic data patterns found in ingest…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ableError to fallback to mock data. """  import os import r…”; code/verify_no_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…or("VERIFICATION FAILED: Synthetic data patterns found in ingest…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/download_dataset.py   # creates data/raw/metalic_glass_raw.csv; 8 command(s) failed: python code/ingest.py               # writes data/processed/cleaned_data.csv (rc=1); python code/descriptors.py (rc=1); python code/train.py (rc=1); 2 declared deliverable(s) absent: data/processed/correlation_matrix.csv; data/processed/vif_diagnostic_log.json

## Failing / missing run-book commands

- python code/download_dataset.py   # creates data/raw/metalic_glass_raw.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-342-predicting-the-influence-of-alloying-on-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/download_dataset.py': [Errno 2] No such file or directory

- python code/ingest.py               # writes data/processed/cleaned_data.csv -> rc=1
-of-alloying-on-/code/zenodo_client.py", line 49, in download_csv_from_zenodo
    raise DataUnavailableError(f"No CSV file found in Zenodo record {doi}")
zenodo_client.DataUnavailableError: No CSV file found in Zenodo record 10.5281/zenodo.11023456

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/ingest.py", line 223, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/ingest.py", line 220, in main
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/resource_monitor.py", line 320, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/ingest.py", line 138, in run_ingestion
    raise DataUnavailableError("Both primary and fallback DOIs are unavailable.") from fe
zenodo_client.DataUnavailableError: Both primary and fallback DOIs are unavailable.

- python code/descriptors.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/descriptors.py", line 252, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/descriptors.py", line 249, in main
    run_descriptors()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/resource_monitor.py", line 320, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/descriptors.py", line 238, in run_descriptors
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/data/processed/cleaned_mg.csv

- python code/train.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/train.py", line 222, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/train.py", line 219, in main
    run_training_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/train.py", line 205, in run_training_pipeline
    raise FileNotFoundError(f"Input data file not found: {data_path}")
FileNotFoundError: Input data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/data/processed/descriptors.csv

- python code/analyze.py -> rc=1
model_path)
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/analyze.py", line 72, in load_model
    raise FileNotFoundError(f"Model file not found at {model_path}")
FileNotFoundError: Model file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/artifacts/models/best_model.pkl

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/analyze.py", line 279, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/analyze.py", line 233, in main
    model = load_model(model_path)
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/analyze.py", line 72, in load_model
    raise FileNotFoundError(f"Model file not found at {model_path}")
FileNotFoundError: Model file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/artifacts/models/best_model.pkl

- python code/report.py -> rc=1
elation matrix from /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/data/processed/correlation_matrix.csv
2026-10-22 14:24:15,981 - ERROR - Input file missing: Correlation matrix file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/data/processed/correlation_matrix.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/report.py", line 230, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/report.py", line 214, in main
    df = load_correlation_matrix(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/report.py", line 58, in load_correlation_matrix
    raise FileNotFoundError(f"Correlation matrix file not found: {csv_path}")
FileNotFoundError: Correlation matrix file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/data/processed/correlation_matrix.csv

- python code/descriptors.py && python code/train.py && python code/analyze.py && python code/report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/descriptors.py", line 252, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/descriptors.py", line 249, in main
    run_descriptors()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/resource_monitor.py", line 320, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/descriptors.py", line 238, in run_descriptors
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/data/processed/cleaned_mg.csv

- python -m pytest tests/unit/ -> rc=2
ure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_zenodo_client.py:15: in <module>
    from zenodo_client import fetch_from_zenodo, DataUnavailableError, DataInsufficientError
E   ImportError: cannot import name 'fetch_from_zenodo' from 'zenodo_client' (/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/zenodo_client.py)
=========================== short test summary info ============================
ERROR tests/unit/test_analyze.py
ERROR tests/unit/test_descriptors_io.py
ERROR tests/unit/test_ingest.py
ERROR tests/unit/test_ingest_retention.py
ERROR tests/unit/test_ingest_stats.py
ERROR tests/unit/test_ingest_t014.py
ERROR tests/unit/test_train_artifacts.py
ERROR tests/unit/test_train_lofo.py
ERROR tests/unit/test_verify_resource_compliance.py
ERROR tests/unit/test_zenodo_client.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 1.20s ==============================


- python -m pytest tests/integration/ -> rc=2
le>
    from ingest import load_and_validate_data, clean_data
E   ImportError: cannot import name 'load_and_validate_data' from 'ingest' (/home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/code/ingest.py)
=============================== warnings summary ===============================
tests/integration/test_train_pipeline.py:84
  /home/runner/work/llmXive/llmXive/projects/PROJ-342-predicting-the-influence-of-alloying-on-/tests/integration/test_train_pipeline.py:84: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_data_ingestion.py
ERROR tests/integration/test_statistical_validation.py
ERROR tests/integration/test_train_cv.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 3 errors in 1.15s =========================



## Declared deliverables still missing

- data/processed/correlation_matrix.csv
- data/processed/vif_diagnostic_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

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
