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

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/data_ingestion/download.py: synthetic/fake INPUT data not authorized by the spec — “…etwork errors and return synthetic data.     - No fallback to mo…”; code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…suggesting synthetic or fake data.          Args:…”; code/data_ingestion/sanity_check.py: synthetic/fake INPUT data not authorized by the spec — “…erns that might indicate synthetic data.          Args:…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/data/ingest.py --species Arabidopsis --stress Drought; python code/data/preprocess.py; python code/models/evaluate.py --train_stress Drought --test_stress Salinity; 3 command(s) failed: python code/modeling/train.py --model random_forest --cv_folds 5 (rc=1); python code/modeling/train.py --model svr --cv_folds 5 (rc=1); python code/reporting/plots.py (rc=1)

## Failing / missing run-book commands

- python code/data/ingest.py --species Arabidopsis --stress Drought -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data/ingest.py': [Errno 2] No such file or directory

- python code/data/preprocess.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/data/preprocess.py': [Errno 2] No such file or directory

- python code/modeling/train.py --model random_forest --cv_folds 5 -> rc=1
rojects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/sklearn/utils/_param_validation.py", line 14, in <module>
    from scipy.sparse import csr_array, issparse
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/__init__.py", line 307, in <module>
    from ._base import *
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/_base.py", line 8, in <module>
    from ._sputils import (asmatrix, check_reshape_kwargs, check_shape,
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/_sputils.py", line 10, in <module>
    from scipy._lib._util import np_long, np_ulong
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/_lib/_util.py", line 22, in <module>
    from numpy.exceptions import AxisError
ModuleNotFoundError: No module named 'numpy.exceptions'

- python code/modeling/train.py --model svr --cv_folds 5 -> rc=1
rojects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/sklearn/utils/_param_validation.py", line 14, in <module>
    from scipy.sparse import csr_array, issparse
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/__init__.py", line 307, in <module>
    from ._base import *
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/_base.py", line 8, in <module>
    from ._sputils import (asmatrix, check_reshape_kwargs, check_shape,
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/_sputils.py", line 10, in <module>
    from scipy._lib._util import np_long, np_ulong
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/_lib/_util.py", line 22, in <module>
    from numpy.exceptions import AxisError
ModuleNotFoundError: No module named 'numpy.exceptions'

- python code/models/evaluate.py --train_stress Drought --test_stress Salinity -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/models/evaluate.py': [Errno 2] No such file or directory

- python code/reporting/plots.py -> rc=1
.11.17/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/__init__.py", line 307, in <module>
    from ._base import *
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/_base.py", line 8, in <module>
    from ._sputils import (asmatrix, check_reshape_kwargs, check_shape,
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/sparse/_sputils.py", line 10, in <module>
    from scipy._lib._util import np_long, np_ulong
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-predicting-plant-stress-response-from-pu/code/.venv/lib/python3.11/site-packages/scipy/_lib/_util.py", line 22, in <module>
    from numpy.exceptions import AxisError
ModuleNotFoundError: No module named 'numpy.exceptions'

