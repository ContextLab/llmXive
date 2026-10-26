# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- scripts/profile_model.py: synthetic/fake INPUT data not authorized by the spec — “…# Run inference on dummy input         dummy_text = "Th…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: scripts/profile_model.py: synthetic/fake INPUT data not authorized by the spec — “…# Run inference on dummy input         dummy_text = "Th…”; 1 run-book script(s) missing (plan/impl path mismatch): python src/stats/comparison.py --run-full; 6 command(s) failed: python src/utils/data_loader.py (rc=1); python code/cli/run_evaluation.py --mode gatekeeper --domains medical,office,education,household (rc=1); python code/cli/run_evaluation.py --mode retrieval_only --domains medical,office,education,household (rc=1)

## Failing / missing run-book commands

- python src/utils/data_loader.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/src/utils/data_loader.py", line 15, in <module>
    from src.utils.config import (
ImportError: cannot import name 'DATASET_ID' from 'src.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/src/utils/config.py)

- python code/cli/run_evaluation.py --mode gatekeeper --domains medical,office,education,household -> rc=1
ast):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/cli/run_evaluation.py", line 17, in <module>
    from code.data.loader import fetch_gatemem
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/loader.py", line 5, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/cli/run_evaluation.py --mode retrieval_only --domains medical,office,education,household -> rc=1
ast):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/cli/run_evaluation.py", line 17, in <module>
    from code.data.loader import fetch_gatemem
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/loader.py", line 5, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/cli/run_evaluation.py --mode long_context --domains medical,office,education,household -> rc=1
ast):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/cli/run_evaluation.py", line 17, in <module>
    from code.data.loader import fetch_gatemem
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/loader.py", line 5, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/stats/comparison.py --run-full -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/src/stats/comparison.py': [Errno 2] No such file or directory

- python code/cli/run_evaluation.py --generate-output -> rc=1
ast):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/cli/run_evaluation.py", line 17, in <module>
    from code.data.loader import fetch_gatemem
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/code/data/loader.py", line 5, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-830-llmxive-follow-up-extending-gatemem-benc/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest -v -> rc=2
sts/contract/test_gatekeeper.py
ERROR tests/contract/test_results_schema.py
ERROR tests/contract/test_results_schema_integration.py
ERROR tests/contract/test_stats_schema.py
ERROR tests/gatekeeper/test_classifiers.py
ERROR tests/gatekeeper/test_rules_malformed.py
ERROR tests/integration/test_pipeline.py
ERROR tests/integration/test_t020_access_control_medical.py
ERROR tests/integration/test_us1_integration.py
ERROR tests/integration/test_us1_medical_domain.py
ERROR tests/integration/test_us1_medical_pipeline.py
ERROR tests/integration/test_utility_education.py
ERROR tests/integration/test_utility_integration.py
ERROR tests/test_baseline_pipeline.py
ERROR tests/unit/test_classifier_mapping.py
ERROR tests/unit/test_classifiers.py
ERROR tests/unit/test_lint_config.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_loader.py
ERROR tests/unit/test_pipeline.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_stats_stratified.py
ERROR tests/unit/test_verify_deps.py
ERROR tests/us3/test_profiling_integration.py
!!!!!!!!!!!!!!!!!!! Interrupted: 26 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 26 errors in 6.35s ========================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
