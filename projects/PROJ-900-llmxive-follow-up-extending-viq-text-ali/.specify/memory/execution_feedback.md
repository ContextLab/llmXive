# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/correlation_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…task requirements      # Simulated data for demonstration     #…”
- code/train.py: synthetic/fake INPUT data not authorized by the spec — “…device          # Create dummy input     dummy_input = torch.…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/correlation_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…task requirements      # Simulated data for demonstration     #…”; code/train.py: synthetic/fake INPUT data not authorized by the spec — “…device          # Create dummy input     dummy_input = torch.…”; 5 command(s) failed: python code/data_loader.py --download-only (rc=1); python code/train.py --config code/config.py (rc=1); python code/eval.py --checkpoint code/codebook.pt (rc=1); 8 declared deliverable(s) absent: data/raw/checksums.json; data/results/correlation_plot.png; data/results/embeddings_high_res.h5

## Failing / missing run-book commands

- python code/data_loader.py --download-only -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/data_loader.py", line 19, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.0

- python code/train.py --config code/config.py -> rc=1
recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/train.py", line 22, in <module>
    from data_loader import get_coco_iterator
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/data_loader.py", line 19, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.0

- python code/eval.py --checkpoint code/codebook.pt -> rc=1
e_output=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/bin/python', 'code/train.py', '--config', 'code/config.py']' returned non-zero exit status 1.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py", line 123, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py", line 88, in main
    run_command(train_cmd, "Training (Codebook Initialization)")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py", line 35, in run_command
    raise RuntimeError(f"Pipeline step failed: {description}") from e
RuntimeError: Pipeline step failed: Training (Codebook Initialization)

- python code/analysis.py -> rc=1
2026-10-26 06:38:08,850 - INFO - Starting Correlation Analysis (T022)
2026-10-26 06:38:08,850 - INFO - Computing texture complexity and PSNR for images in data/processed/ground_truth_images
2026-10-26 06:38:08,850 - ERROR - Failed to load data: No PNG images found in ground truth directory.


- python -m pytest tests/ -v -> rc=2
module>
    from code.data_loader import load_coco_streaming, load_imagenet_batched, validate_exclusions
code/data_loader.py:19: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/datasets/__init__.py:22: in <module>
    from .arrow_dataset import Dataset
../../.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-900-llmxive-follow-up-extending-viq-text-ali/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.0
=========================== short test summary info ============================
ERROR tests/integration/test_eval.py
ERROR tests/test_data.py
ERROR tests/test_data_loader.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.46s ===============================



## Declared deliverables still missing

- data/raw/checksums.json
- data/results/correlation_plot.png
- data/results/embeddings_high_res.h5
- data/results/fidelity_metrics.json
- data/results/semantic_baseline.json
- data/results/semantic_diff.json
- data/results/semantic_high_res.json
- data/results/train_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/extract_native_images.py` — NOT invoked by the run-book
    - `code/verify_data_integrity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_analysis.py` — NOT invoked by the run-book
    - `code/eval.py` — IS a run-book command
  Make ONE of these WRITE `data/results/correlation_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/embeddings_high_res.h5` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_fidelity_metrics.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/eval.py` — IS a run-book command
    - `code/eval_high_res.py` — NOT invoked by the run-book
    - `code/eval_semantic.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/embeddings_high_res.h5` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_fidelity_metrics.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/correlation_analysis.py` — NOT invoked by the run-book
    - `code/eval.py` — IS a run-book command
  Make ONE of these WRITE `data/results/fidelity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/semantic_baseline.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/semantic_diff_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/semantic_baseline.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/semantic_diff.json` is declared but was NOT written. Scripts referencing it:
    - `code/semantic_diff_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/semantic_diff.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/semantic_high_res.json` is declared but was NOT written. Scripts referencing it:
    - `code/eval_semantic.py` — NOT invoked by the run-book
    - `code/semantic_diff_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/semantic_high_res.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/train_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/results/train_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
