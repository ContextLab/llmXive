# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/executor.py: self-declared fabricated metric — “…ction time                  # Mock result for demonstration if no real…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/utils/io.py --verify-checksums`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/executor.py: self-declared fabricated metric — “…ction time                  # Mock result for demonstration if no real…”; 9 command(s) failed: python code/src/main.py --stage download (rc=1); python code/src/main.py --stage embed --tasks 18 (rc=1); python code/src/main.py --stage plan --tasks 18 (rc=1); 2 declared deliverable(s) absent: data/interim/baseline_results.parquet; data/interim/execution_logs.parquet

## Failing / missing run-book commands

- python code/src/main.py --stage download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/main.py --stage embed --tasks 18 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/main.py --stage plan --tasks 18 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/main.py --stage execute --mode oracle -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/main.py --stage execute --mode real -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/main.py --stage baseline_gpu --subset 5 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/src/main.py --stage analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 24, in <module>
    from src.vision_encoder import create_vision_encoder
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/vision_encoder.py", line 8, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/utils/io.py --verify-checksums -> rc=1

2026-10-31 14:08:26,271 INFO __main__: Attempting to load primary RoboDojo dataset: RoboDojo/robodojo
2026-10-31 14:08:26,369 INFO httpx2: HTTP Request: GET https://huggingface.co/api/datasets/RoboDojo/robodojo "HTTP/1.1 401 Unauthorized"
2026-10-31 14:08:26,370 WARNING __main__: Primary dataset load failed (Dataset 'RoboDojo/robodojo' doesn't exist on the Hub or cannot be accessed.). Trying public fallback.
2026-10-31 14:08:26,370 INFO __main__: Attempting to load fallback dataset: RoboDojo/robodojo-public-mirror
2026-10-31 14:08:26,420 INFO httpx2: HTTP Request: GET https://huggingface.co/api/datasets/RoboDojo/robodojo-public-mirror "HTTP/1.1 401 Unauthorized"
2026-10-31 14:08:26,420 ERROR __main__: Both primary and fallback dataset loads failed: Dataset 'RoboDojo/robodojo' doesn't exist on the Hub or cannot be accessed. | Dataset 'RoboDojo/robodojo-public-mirror' doesn't exist on the Hub or cannot be accessed.
2026-10-31 14:08:26,421 ERROR __main__: Failed to load RoboDojo dataset: Unable to fetch RoboDojo dataset from any known public source.
2026-10-31 14:08:26,421 ERROR __main__: Dataset streaming failed: Unable to fetch RoboDojo dataset

- python -c "import pandas as pd; print(pd.read_parquet('data/interim/execution_logs.parquet').head())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 667, in read_parquet
    return impl.read(
           ^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 267, in read
    path_or_handle, handles, filesystem = _get_path_or_handle(
                                          ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 140, in _get_path_or_handle
    handles = get_handle(
              ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 882, in get_handle
    handle = open(handle, ioargs.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/interim/execution_logs.parquet'

- python -m pytest code/tests/ -v -> rc=2
pt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/unit/test_vision_encoder.py:9: in <module>
    import torch
E   ModuleNotFoundError: No module named 'torch'
=========================== short test summary info ============================
ERROR code/tests/contract/test_execution_outcome.py
ERROR code/tests/integration/test_executor_logging.py
ERROR code/tests/integration/test_failure_logging.py
ERROR code/tests/integration/test_gap_analysis.py
ERROR code/tests/integration/test_planner.py
ERROR code/tests/integration/test_report.py
ERROR code/tests/unit/test_config.py
ERROR code/tests/unit/test_controller_adapter.py
ERROR code/tests/unit/test_data_loader.py
ERROR code/tests/unit/test_executor.py
ERROR code/tests/unit/test_oracle_executor.py
ERROR code/tests/unit/test_planner.py
ERROR code/tests/unit/test_stats.py
ERROR code/tests/unit/test_stats_analysis.py
ERROR code/tests/unit/test_vision_encoder.py
!!!!!!!!!!!!!!!!!!! Interrupted: 15 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 15 errors in 1.24s ==============================



## Declared deliverables still missing

- data/interim/baseline_results.parquet
- data/interim/execution_logs.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/baseline_results.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats_analysis.py` — NOT invoked by the run-book
    - `code/tests/integration/test_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/baseline_results.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/execution_logs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/executor.py` — NOT invoked by the run-book
    - `code/src/stats_analysis.py` — NOT invoked by the run-book
    - `code/tests/integration/test_executor_logging.py` — NOT invoked by the run-book
    - `code/tests/integration/test_failure_logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/execution_logs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
