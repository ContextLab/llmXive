# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…e, never falling back to synthetic data. """ import os import nu…”
- data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…# Dummy Data Directory  This director…”
- data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…pt will generate its own dummy data dynamically in a tempora…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…e, never falling back to synthetic data. """ import os import nu…”; data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…# Dummy Data Directory  This director…”; data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…pt will generate its own dummy data dynamically in a tempora…”; 6 command(s) failed: bash scripts/pre-run-validation.sh (rc=1); python code/main.py (rc=1); python code/main.py --step preprocess (rc=1)

## Failing / missing run-book commands

- bash scripts/pre-run-validation.sh -> rc=1
=== Pre-run Validation ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f
Checking citations...

2026-10-12 19:23:48,441 ERROR __main__: Missing required citations:
2026-10-12 19:23:48,441 ERROR __main__:   - doi:10.1234/example1
2026-10-12 19:23:48,441 ERROR __main__:   - doi:10.5678/example2

- python code/main.py -> rc=1
me/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py:10: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 26, in <module>
    from preprocessing import preprocess_all_participants
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 32, in <module>
    from mne.time_frequency import psd_welch
ImportError: cannot import name 'psd_welch' from 'mne.time_frequency' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/mne/time_frequency/__init__.py)

- python code/main.py --step preprocess -> rc=1
me/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py:10: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 26, in <module>
    from preprocessing import preprocess_all_participants
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 32, in <module>
    from mne.time_frequency import psd_welch
ImportError: cannot import name 'psd_welch' from 'mne.time_frequency' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/mne/time_frequency/__init__.py)

- python code/main.py --step model -> rc=1
me/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py:10: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 26, in <module>
    from preprocessing import preprocess_all_participants
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 32, in <module>
    from mne.time_frequency import psd_welch
ImportError: cannot import name 'psd_welch' from 'mne.time_frequency' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/mne/time_frequency/__init__.py)

- python code/main.py --step diagnostics -> rc=1
me/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py:10: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 26, in <module>
    from preprocessing import preprocess_all_participants
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 32, in <module>
    from mne.time_frequency import psd_welch
ImportError: cannot import name 'psd_welch' from 'mne.time_frequency' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/mne/time_frequency/__init__.py)

- python -m pytest tests/ -v -> rc=2
b/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_feature_aggregation.py
ERROR tests/integration/test_permutation.py
ERROR tests/integration/test_pipeline.py
ERROR tests/test_config.py
ERROR tests/unit/test_checksum_manager.py
ERROR tests/unit/test_data_loader.py
ERROR tests/unit/test_preprocessing.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 14 warnings, 7 errors in 2.04s ========================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
