# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…""Create a deterministic synthetic dataset.      Parameters     ---…”
- code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Execute the full synthetic data pipeline.      The funct…”
- code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…---------------     # 2. Generate synthetic dataset     # ----------…”
- code/modeling/train.py: synthetic/fake INPUT data not authorized by the spec — “…lse:         # Fallback: generate synthetic p-values for demonstrati…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…""Create a deterministic synthetic dataset.      Parameters     ---…”; code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Execute the full synthetic data pipeline.      The funct…”; code/data/pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…---------------     # 2. Generate synthetic dataset     # ----------…”; 4 command(s) failed: python code/data/extract_metrics.py (rc=2); python code/data/preprocess.py (rc=2); python code/modeling/train.py (rc=2)

## Failing / missing run-book commands

- python code/data/extract_metrics.py -> rc=2
    usage: extract_metrics.py [-h] --input INPUT --output OUTPUT
                          [--extension EXTENSION] [--chunk-size CHUNK_SIZE]
extract_metrics.py: error: the following arguments are required: --input, --output
- python code/data/preprocess.py -> rc=2
    usage: preprocess.py [-h] --input INPUT --output OUTPUT
                     [--ground-truth GROUND_TRUTH]
                     [--min-precision MIN_PRECISION]
preprocess.py: error: the following arguments are required: --input, --output
- python code/modeling/train.py -> rc=2
    usage: train.py [-h] --data-dir DATA_DIR [--model-dir MODEL_DIR] [--seed SEED]
                [--alpha ALPHA]
train.py: error: the following arguments are required: --data-dir
- python code/modeling/evaluate.py -> rc=1
    2026-07-15 09:25:14,653 - __main__ - INFO - Starting evaluation for model: primary
2026-07-15 09:25:14,653 - __main__ - ERROR - Evaluation failed: Test data file not found at data/test_data.csv. Please run the data pipeline first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/modeling/evaluate.py", line 209, in main
    metrics, cal_path, roc_path = evaluate_model(args.model)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/modeling/evaluate.py", line 140, in evaluate_model
    X, y, feature_names = load_test_data()
                          ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-148-statistical-analysis-of-code-complexity-/code/modeling/evaluate.py", line 34, in load_test_data
    raise FileNotFoundError(f"Test data file not found at {test_path}. "
FileNotFoundError: Test data file not found at data/test_data.csv. Please run the data pipeline first.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/test_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/modeling/evaluate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/test_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/modeling/evaluate.py`.
