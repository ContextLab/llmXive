# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…""Create a deterministic synthetic dataset.      Parameters     ---…”
- code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Execute the full synthetic data pipeline.      The funct…”
- code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…---------------     # 2. Generate synthetic dataset     # ----------…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/extract_metrics.py`
  - script usage: `extract_metrics.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `extract_metrics.py: error: the following arguments are required: --input, --output`
- run-book command: `python code/data/preprocess.py`
  - script usage: `preprocess.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `preprocess.py: error: the following arguments are required: --input, --output`
- run-book command: `python code/modeling/train.py`
  - script usage: `train.py [-h] --data-dir DATA_DIR [--model-dir MODEL_DIR] [--seed SEED]`
  - argparse error: `train.py: error: the following arguments are required: --data-dir`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…""Create a deterministic synthetic dataset.      Parameters     ---…”; code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Execute the full synthetic data pipeline.      The funct…”; code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…---------------     # 2. Generate synthetic dataset     # ----------…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/data/label_bugs.py; 6 command(s) failed: python code/data/download_gh.py (rc=1); python code/data/extract_metrics.py (rc=2); python code/data/preprocess.py (rc=2); 1 declared deliverable(s) absent: data/model/thresholds.csv

## Failing / missing run-book commands

- python code/data/download_gh.py -> rc=1
leapis.com/gh-projects/manifests/java-projects.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/data/download_gh.py", line 308, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/data/download_gh.py", line 304, in main
    run_download_pipeline(output_dir=output_path, project_count=args.project_count)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/data/download_gh.py", line 219, in run_download_pipeline
    manifest = fetch_manifest()
               ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/data/download_gh.py", line 83, in fetch_manifest
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://storage.googleapis.com/gh-projects/manifests/java-projects.json

- python code/data/extract_metrics.py -> rc=2

usage: extract_metrics.py [-h] --input INPUT --output OUTPUT
                          [--extension EXTENSION] [--chunk-size CHUNK_SIZE]
                          [--seed SEED]
extract_metrics.py: error: the following arguments are required: --input, --output

- python code/data/label_bugs.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-148-statistical-analysis-of-code-complexity-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/data/label_bugs.py': [Errno 2] No such file or directory

- python code/data/preprocess.py -> rc=2

usage: preprocess.py [-h] --input INPUT --output OUTPUT
                     [--ground-truth GROUND_TRUTH]
                     [--min-precision MIN_PRECISION] [--seed SEED]
preprocess.py: error: the following arguments are required: --input, --output

- python code/modeling/train.py -> rc=2

usage: train.py [-h] --data-dir DATA_DIR [--model-dir MODEL_DIR] [--seed SEED]
                [--alpha ALPHA]
train.py: error: the following arguments are required: --data-dir

- python code/modeling/evaluate.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/modeling/evaluate.py", line 16, in <module>
    from sklearn.metrics import (
ImportError: cannot import name 'calibration_curve' from 'sklearn.metrics' (/home/runner/.cache/llmxive/base-env/py311-6f1866971868/sklearn/metrics/__init__.py)

- python -m pytest tests/contract/ -> rc=1
t/test_bug_label_validation.py:153: TypeError
=========================== short test summary info ============================
FAILED tests/contract/test_bug_label_validation.py::TestBugLabelValidation::test_precision_above_threshold
FAILED tests/contract/test_bug_label_validation.py::TestBugLabelValidation::test_precision_below_threshold_fails
FAILED tests/contract/test_bug_label_validation.py::TestBugLabelValidation::test_empty_predicted_positives
FAILED tests/contract/test_bug_label_validation.py::TestBugLabelValidation::test_invalid_column_names
FAILED tests/contract/test_bug_label_validation.py::TestBugLabelValidation::test_integration_with_realistic_distribution
FAILED tests/contract/test_bug_label_validation.py::TestBugLabelValidation::test_exact_threshold_boundary
ERROR tests/contract/test_baseline_roc_auc.py::test_baseline_roc_auc
ERROR tests/contract/test_dataset_schema.py::test_dataset_schema
ERROR tests/contract/test_evaluation_metrics.py::test_evaluation_metrics
ERROR tests/contract/test_fdr.py::test_fdr_threshold
ERROR tests/contract/test_model_output_schema.py::test_model_output_schema
========================= 6 failed, 5 errors in 0.50s ==========================



## Declared deliverables still missing

- data/model/thresholds.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/model/thresholds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/generate_thresholds.py` — NOT invoked by the run-book
    - `code/modeling/pipeline.py` — NOT invoked by the run-book
    - `code/report/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/model/thresholds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
