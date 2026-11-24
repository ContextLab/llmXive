# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/feasibility_check.py: self-declared fabricated metric — “…the diffusion steps. Here we simulate      the latency impact by artificially introd…”
- code/utils/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…ricates or falls back to synthetic data. If the real Hugging Fac…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/feasibility_check.py: self-declared fabricated metric — “…the diffusion steps. Here we simulate      the latency impact by artificially introd…”; code/utils/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…ricates or falls back to synthetic data. If the real Hugging Fac…”; 1 run-book script(s) missing (plan/impl path mismatch): python train.py --input data/processed/gsm8k_features.jsonl --target B_star --models xgboost,random_forest,decision_tree --split 0.8 --task classification; 5 command(s) failed: python code/sweep.py --dataset gsmk --block-sizes 1,2,4,8,16,32 --samples 500 --seed 42 (rc=1); python code/features.py --dataset gsm8k --input data/processed/gsm8k_ground_truth.jsonl --output data/processed/gsm8k_features.jsonl (rc=1); python code/evaluate.py --models data/models/ --test-data data/processed/humaneval_features.jsonl --metrics accuracy,f1,correlation,generalization (rc=1); 1 declared deliverable(s) absent: data/processed/correlation_report.json

## Failing / missing run-book commands

- python code/sweep.py --dataset gsmk --block-sizes 1,2,4,8,16,32 --samples 500 --seed 42 -> rc=1
ive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/sweep.py", line 49, in <module>
    from utils.data_loader import load_gsm8k_streaming, load_humaneval_streaming
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/utils/data_loader.py", line 12, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/features.py --dataset gsm8k --input data/processed/gsm8k_ground_truth.jsonl --output data/processed/gsm8k_features.jsonl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/features.py", line 10, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python train.py --input data/processed/gsm8k_features.jsonl --target B_star --models xgboost,random_forest,decision_tree --split 0.8 --task classification -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/train.py': [Errno 2] No such file or directory

- python code/evaluate.py --models data/models/ --test-data data/processed/humaneval_features.jsonl --metrics accuracy,f1,correlation,generalization -> rc=1
home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/evaluate.py", line 10, in <module>
    from utils.data_loader import load_dataset_streaming
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/code/utils/data_loader.py", line 12, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest tests/contract/ -> rc=2
, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 4 items / 1 error

==================================== ERRORS ====================================
_______________ ERROR collecting tests/contract/test_schemas.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/tests/contract/test_schemas.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_schemas.py:8: in <module>
    from pydantic import ValidationError
E   ModuleNotFoundError: No module named 'pydantic'
=========================== short test summary info ============================
ERROR tests/contract/test_schemas.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.10s ===============================


- python -m pytest tests/integration/ -> rc=2
7/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_sweep_logic.py:23: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/__init__.py:17: in <module>
    from .arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-986-llmxive-follow-up-extending-blockpilot-i/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/integration/test_sweep_logic.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.50s ===============================



## Declared deliverables still missing

- data/processed/correlation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/correlation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
