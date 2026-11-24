# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_ingestion/download.py: synthetic/fake INPUT data not authorized by the spec — “…etwork errors and return synthetic data.     - No fallback to mo…”
- code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…suggesting synthetic or fake data.          Args:…”
- code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…erns that might indicate synthetic data.          Args:…”
- code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…ECK FAILED: Synthetic or fake data detected!")         logg…”
- code/reporting/metrics.py: synthetic/fake INPUT data not authorized by the spec — “…ross all columns. Likely mock data.")         elif arr.ndim…”
- code/reporting/metrics.py: synthetic/fake INPUT data not authorized by the spec — “…as zero variance. Likely mock data.")                  retu…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/modeling/train.py --model random_forest --cv_folds 5`
  - script usage: `train.py [-h] [--strategy STRATEGY]`
  - argparse error: `train.py: error: unrecognized arguments: --model random_forest --cv_folds 5`
- run-book command: `python code/modeling/train.py --model svr --cv_folds 5`
  - script usage: `train.py [-h] [--strategy STRATEGY]`
  - argparse error: `train.py: error: unrecognized arguments: --model svr --cv_folds 5`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/data_ingestion/download.py: synthetic/fake INPUT data not authorized by the spec — “…etwork errors and return synthetic data.     - No fallback to mo…”; code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…suggesting synthetic or fake data.          Args:…”; code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…erns that might indicate synthetic data.          Args:…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/data/preprocess.py --mode fit_transform; python code/models/evaluate.py --train_stress Drought --test_stress Salinity; python code/models/train_classifier.py --model random_forest; 3 command(s) failed: python code/data/ingest.py --species Arabidopsis --stress Drought (rc=1); python code/modeling/train.py --model random_forest --cv_folds 5 (rc=2); python code/modeling/train.py --model svr --cv_folds 5 (rc=2)

## Failing / missing run-book commands

- python code/data/ingest.py --species Arabidopsis --stress Drought -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data/ingest.py", line 22, in <module>
    from code.data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data/download.py", line 18, in <module>
    from data_ingestion.download import download_file
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data_ingestion/__init__.py", line 6, in <module>
    from .verify_sources import parse_citations, fetch_doi_metadata, fetch_url_metadata, calculate_token_overlap, verify_semantic_relevance, validate_citation, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data_ingestion/verify_sources.py", line 38, in <module>
    setup_logging(level=LOG_LEVEL, log_path=LOG_PATH)
TypeError: setup_logging() got an unexpected keyword argument 'level'

- python code/data/preprocess.py --mode fit_transform -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-267-predicting-plant-stress-response-from-pu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data/preprocess.py': [Errno 2] No such file or directory

- python code/modeling/train.py --model random_forest --cv_folds 5 -> rc=2

usage: train.py [-h] [--strategy STRATEGY]
train.py: error: unrecognized arguments: --model random_forest --cv_folds 5

- python code/modeling/train.py --model svr --cv_folds 5 -> rc=2

usage: train.py [-h] [--strategy STRATEGY]
train.py: error: unrecognized arguments: --model svr --cv_folds 5

- python code/models/evaluate.py --train_stress Drought --test_stress Salinity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-267-predicting-plant-stress-response-from-pu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/models/evaluate.py': [Errno 2] No such file or directory

- python code/models/train_classifier.py --model random_forest -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-267-predicting-plant-stress-response-from-pu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/models/train_classifier.py': [Errno 2] No such file or directory

- python code/tasks/schema_validate.py  --dataset contracts/dataset.schema.yaml  --model_output contracts/model_output.schema.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-267-predicting-plant-stress-response-from-pu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/tasks/schema_validate.py': [Errno 2] No such file or directory

