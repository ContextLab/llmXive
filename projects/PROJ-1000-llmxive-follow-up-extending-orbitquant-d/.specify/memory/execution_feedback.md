# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”
- code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”
- code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”
- code/run_quantization_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# We'll create a dummy input to the model's main bloc…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode full`
  - script usage: `main.py [-h] --phase {init,validate}`
  - argparse error: `main.py: error: the following arguments are required: --phase`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download_coco.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”; code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”; code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”; 4 command(s) failed: python code/data/download_coco.py (rc=1); python code/main.py --mode full (rc=2); python -m pytest tests/unit/ (rc=2); 6 declared deliverable(s) absent: data/processed/clustering_report.json; data/processed/correlation_results.json; data/processed/diverse_prompts.csv

## Failing / missing run-book commands

- python code/data/download_coco.py -> rc=1
k/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/download_coco.py", line 136, in main
    for record in _stream_coco_captions():
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/download_coco.py", line 66, in _stream_coco_captions
    raise RuntimeError(f"Failed to load COCO captions dataset: {e}") from e
RuntimeError: Failed to load COCO captions dataset: Dataset 'nlpconnect/coco_captions' doesn't exist on the Hub or cannot be accessed.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/download_coco.py", line 166, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/data/download_coco.py", line 161, in main
    raise RuntimeError(f"Failed to stream COCO captions: {e}") from e
RuntimeError: Failed to stream COCO captions: Failed to load COCO captions dataset: Dataset 'nlpconnect/coco_captions' doesn't exist on the Hub or cannot be accessed.

- python code/main.py --mode full -> rc=2

usage: main.py [-h] --phase {init,validate}
main.py: error: the following arguments are required: --phase

- python -m pytest tests/unit/ -> rc=2
lidate_clustering.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_validate_clustering.py:15: in <module>
    from validation.validate_clustering import (
E   ImportError: cannot import name 'REQUIRED_TOP_LEVEL_KEYS' from 'validation.validate_clustering' (/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/code/validation/validate_clustering.py)
=========================== short test summary info ============================
ERROR tests/unit/test_clustering.py - FileNotFoundError: [Errno 2] No such fi...
ERROR tests/unit/test_load_matrices.py
ERROR tests/unit/test_router_inference.py
ERROR tests/unit/test_timing.py - FileNotFoundError: [Errno 2] No such file o...
ERROR tests/unit/test_validate_clustering.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 6.12s ===============================


- python -m pytest tests/integration/ -> rc=2
__ ERROR collecting tests/integration/test_preprocess.py _____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-1000-llmxive-follow-up-extending-orbitquant-d/tests/integration/test_preprocess.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_preprocess.py:21: in <module>
    from data.preprocess import split_data, write_csv, main
E   ModuleNotFoundError: No module named 'data.preprocess'
=========================== short test summary info ============================
ERROR tests/integration/test_activation_variance.py
ERROR tests/integration/test_download_diverse_prompts.py
ERROR tests/integration/test_full_pipeline.py - FileNotFoundError: [Errno 2] ...
ERROR tests/integration/test_preprocess.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 5.60s ===============================



## Declared deliverables still missing

- data/processed/clustering_report.json
- data/processed/correlation_results.json
- data/processed/diverse_prompts.csv
- data/processed/final_evaluation_report.json
- data/processed/prompts.csv
- data/processed/quantized_activations.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clustering_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/load_matrices.py` — NOT invoked by the run-book
    - `code/analysis/mse_validator.py` — NOT invoked by the run-book
    - `code/analysis/router.py` — NOT invoked by the run-book
    - `code/analysis/router_api_docs.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/main_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clustering_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main_validation.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/validation/validate_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/diverse_prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/entropy_proxy.py` — NOT invoked by the run-book
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/evaluation/timing.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_router_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/diverse_prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_evaluation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistical_test.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_evaluation_modular.py` — NOT invoked by the run-book
    - `code/utils/data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_evaluation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/entropy_proxy.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/download_coco.py` — IS a run-book command
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/quantized_activations.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/mse_validator.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/quantization/static_baseline.py` — NOT invoked by the run-book
    - `code/quantization/w2a4_engine.py` — NOT invoked by the run-book
    - `code/run_quantization_validation.py` — NOT invoked by the run-book
    - `code/utils/data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/quantized_activations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
