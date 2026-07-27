# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluation/metrics.py: function `get_predictions` returns a bare RNG draw (line 29) — a reported value computed from no real input

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/metrics.py: function `get_predictions` returns a bare RNG draw (line 29) — a reported value computed from no real input; 1 run-book script(s) missing (plan/impl path mismatch): python run_full_pipeline.py; 5 command(s) failed: python code/data/download.py --dataset recipe1m --output data/raw/ (rc=1); python code/data/preprocess.py --input data/raw/ --output data/processed/ (rc=1); python code/data/split.py --input data/processed/ingredient_pairs.csv --output data/processed/ (rc=1); 9 declared deliverable(s) absent: data/evaluation_log.json; data/evaluation_metrics.json; data/final/bayesian_results.json

## Failing / missing run-book commands

- python code/data/download.py --dataset recipe1m --output data/raw/ -> rc=1
    Starting dataset download...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/download.py", line 143, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/download.py", line 140, in main
    download_datasets()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/download.py", line 114, in download_datasets
    raise FileNotFoundError("Verification report not found. Run T012 first.")
FileNotFoundError: Verification report not found. Run T012 first.
- python code/data/preprocess.py --input data/raw/ --output data/processed/ -> rc=1
    ive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parquet.py", line 199, in write
    path_or_handle, handles, filesystem = _get_path_or_handle(
                                          ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parquet.py", line 141, in _get_path_or_handle
    handles = get_handle(
              ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 797, in get_handle
    check_parent_directory(str(handle))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 656, in check_parent_directory
    raise OSError(rf"Cannot save file into a non-existent directory: '{parent}'")
OSError: Cannot save file into a non-existent directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/processed'
- python code/data/split.py --input data/processed/ingredient_pairs.csv --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/split.py", line 48, in <module>
    create_train_test_split()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/data/split.py", line 26, in create_train_test_split
    raise FileNotFoundError("final_features.parquet not found. Run T018 first.")
FileNotFoundError: final_features.parquet not found. Run T018 first.
- python code/models/fit_logistic.py --input data/processed/train.csv --output data/logs/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_logistic.py", line 76, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_logistic.py", line 69, in main
    df = load_processed_data()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_logistic.py", line 17, in load_processed_data
    raise FileNotFoundError("train_set.parquet not found.")
FileNotFoundError: train_set.parquet not found.
- python code/models/fit_bayesian.py --input data/processed/train.csv --output data/logs/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_bayesian.py", line 74, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/models/fit_bayesian.py", line 53, in main
    import torch
ModuleNotFoundError: No module named 'torch'
- python run_full_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-175-statistical-analysis-of-publicly-availab/run_full_pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/evaluation_log.json
- data/evaluation_metrics.json
- data/final/bayesian_results.json
- data/final/logistic_results.json
- data/model_fitting_log.json
- data/pipeline_execution_log.json
- data/processed/co_occurrence_matrix.parquet
- data/processed/flavor_similarity.parquet
- data/split_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/evaluation_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/capture_metrics.py` — NOT invoked by the run-book
    - `code/validation/execute_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evaluation_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/evaluation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/validation/execute_full_pipeline.py` — NOT invoked by the run-book
    - `code/validation/execute_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evaluation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final/bayesian_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/fit_bayesian.py` — IS a run-book command
    - `code/validation/execute_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/bayesian_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final/logistic_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/fit_logistic.py` — IS a run-book command
    - `code/evaluation/capture_metrics.py` — NOT invoked by the run-book
    - `code/validation/execute_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/logistic_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/model_fitting_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/capture_metrics.py` — NOT invoked by the run-book
    - `code/validation/execute_model_fitting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/model_fitting_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/pipeline_execution_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluation/capture_metrics.py` — NOT invoked by the run-book
    - `code/validation/execute_full_pipeline.py` — NOT invoked by the run-book
    - `code/validation/execute_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/pipeline_execution_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/co_occurrence_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/validation/execute_full_pipeline.py` — NOT invoked by the run-book
    - `code/validation/execute_pipeline.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/co_occurrence_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/flavor_similarity.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/models/fit_logistic.py` — IS a run-book command
    - `code/models/fit_bayesian.py` — IS a run-book command
    - `code/models/diagnostics.py` — NOT invoked by the run-book
    - `code/validation/execute_full_pipeline.py` — NOT invoked by the run-book
    - `code/validation/execute_pipeline.py` — NOT invoked by the run-book
    - `code/data/verify.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/flavor_similarity.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/split_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/audit_reproducibility.py` — NOT invoked by the run-book
    - `code/validation/execute_pipeline.py` — NOT invoked by the run-book
    - `code/data/split.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/split_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `final_features.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/validation/execute_full_pipeline.py`, `code/validation/execute_pipeline.py`, `code/data/split.py`, `code/data/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `final_features.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/validation/execute_full_pipeline.py`, `code/validation/execute_pipeline.py`, `code/data/split.py`, `code/data/preprocess.py`.

### `train_set.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/fit_logistic.py`, `code/models/fit_bayesian.py`, `code/data/split.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `train_set.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/fit_logistic.py`, `code/models/fit_bayesian.py`, `code/data/split.py`.
