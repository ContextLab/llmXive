# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/download_qm9.py: synthetic/fake INPUT data not authorized by the spec — “…ata.         # We do NOT generate synthetic data.         raise Runt…”
- code/data/download_qm9.py: synthetic/fake INPUT data not authorized by the spec — “…set. Cannot proceed with fake data.")  if __name__ == "__ma…”
- code/data/extract_2d_descriptors.py: synthetic/fake INPUT data not authorized by the spec — “…being installed, we will generate a synthetic     2D feature vector ba…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/download_qm9.py: synthetic/fake INPUT data not authorized by the spec — “…ata.         # We do NOT generate synthetic data.         raise Runt…”; code/data/download_qm9.py: synthetic/fake INPUT data not authorized by the spec — “…set. Cannot proceed with fake data.")  if __name__ == "__ma…”; code/data/extract_2d_descriptors.py: synthetic/fake INPUT data not authorized by the spec — “…being installed, we will generate a synthetic     2D feature vector ba…”; 6 command(s) failed: python code/data/generate_processed_data.py (rc=1); python code/training/train_gnn.py (rc=1); python code/training/train_rf.py (rc=1); 1 declared deliverable(s) absent: data/processed/molecules_10k.parquet

## Failing / missing run-book commands

- python code/data/generate_processed_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/generate_processed_data.py", line 10, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/__init__.py", line 22, in <module>
    from pandas.compat import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.numpy import is_numpy_dev
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/numpy/__init__.py", line 10, in <module>
    _np_version = np.__version__
                  ^^^^^^^^^^^^^^
AttributeError: module 'numpy' has no attribute '__version__'
- python code/training/train_gnn.py -> rc=1
    p as map
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/torch/utils/data/datapipes/iter/__init__.py", line 1, in <module>
    from torch.utils.data.datapipes.iter.callable import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/torch/utils/data/datapipes/iter/callable.py", line 8, in <module>
    from torch.utils.data._utils.collate import default_collate
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/torch/utils/data/_utils/__init__.py", line 53, in <module>
    from . import collate, fetch, pin_memory, signal_handling, worker
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/torch/utils/data/_utils/collate.py", line 330, in <module>
    default_collate_fn_map[np.ndarray] = collate_numpy_array_fn
                           ^^^^^^^^^^
AttributeError: module 'numpy' has no attribute 'ndarray'. Did you mean: 'array'?
- python code/training/train_rf.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py", line 12, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/__init__.py", line 22, in <module>
    from pandas.compat import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.numpy import is_numpy_dev
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/numpy/__init__.py", line 10, in <module>
    _np_version = np.__version__
                  ^^^^^^^^^^^^^^
AttributeError: module 'numpy' has no attribute '__version__'
- python code/analysis/generate_performance_plots.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 29, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/__init__.py", line 22, in <module>
    from pandas.compat import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.numpy import is_numpy_dev
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/numpy/__init__.py", line 10, in <module>
    _np_version = np.__version__
                  ^^^^^^^^^^^^^^
AttributeError: module 'numpy' has no attribute '__version__'
- python code/analysis/generate_significance.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_significance.py", line 30, in <module>
    from analysis.statistical_tests import paired_t_test
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/statistical_tests.py", line 12, in <module>
    from scipy import stats
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/scipy/__init__.py", line 44, in <module>
    from numpy import __version__ as __numpy_version__
ImportError: cannot import name '__version__' from 'numpy' (/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/numpy/__init__.py)
- python code/generate_summary.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 162, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 153, in main
    generate_summary(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 66, in generate_summary
    significance = load_csv_as_dicts(significance_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 25, in load_csv_as_dicts
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
FileNotFoundError: CSV file not found: results/significance.csv

## Declared deliverables still missing

- data/processed/molecules_10k.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/molecules_10k.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/generate_processed_data.py` — IS a run-book command
    - `code/training/train_gnn.py` — IS a run-book command
    - `code/training/train_rf.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/molecules_10k.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `results/significance.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/generate_summary.py`, `code/analysis/generate_significance.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/significance.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/generate_summary.py`, `code/quickstart_validation.py`, `code/analysis/generate_significance.py`.
