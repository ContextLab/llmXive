# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_data.py: self-declared fabricated metric — “…tadata fields are filled with placeholder values.     """     # Metadata – pl…”
- code/generate_data.py: self-declared fabricated metric — “…ues.     """     # Metadata – placeholder values sufficient for validation…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the gene e…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…is no silent fallback to synthetic data.  The script can be exec…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…cessibility matrix – for synthetic data we reuse the same consta…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…schema)     logger.info("Synthetic data conforms to the dataset…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…_path)      logger.info("Synthetic data generation completed suc…”
- code/run_t011.py: synthetic/fake INPUT data not authorized by the spec — “…"""Write log indicating synthetic data was skipped because real…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_data.py: self-declared fabricated metric — “…tadata fields are filled with placeholder values.     """     # Metadata – pl…”; code/generate_data.py: self-declared fabricated metric — “…ues.     """     # Metadata – placeholder values sufficient for validation…”; code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the gene e…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/analyze.py; 6 command(s) failed: python code/download_encode.py --cell-lines GM12878,K562,HMEC,IMR90,HepG2 (rc=1); python code/preprocess.py (rc=1); python code/train.py (rc=1); 7 declared deliverable(s) absent: data/processed/cell_type_specific_genes.csv; data/processed/external_validation_r2.csv; data/processed/housekeeping_genes.csv

## Failing / missing run-book commands

- python code/download_encode.py --cell-lines GM12878,K562,HMEC,IMR90,HepG2 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/download_encode.py", line 16, in <module>
    logging.FileHandler('logs/download_encode.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/logs/download_encode.log'

- python code/preprocess.py -> rc=1
2026-10-20 18:37:41,207 - ERROR - File not found: Peak features file not found: data/processed/tss_binned_features.csv


- python code/train.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/train.py", line 30, in <module>
    logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'training.log'))
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/logs/training.log'

- python code/analyze.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-211-predicting-gene-expression-from-chromati/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/analyze.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
 projects/PROJ-211-predicting-gene-expression-from-chromati/tests/unit/test_train.py _
tests/unit/test_train.py:13: in <module>
    from train import load_variable_peaks, run_cross_validation, train_elastic_net
code/train.py:30: in <module>
    logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'training.log'))
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1181: in __init__
    StreamHandler.__init__(self, self._open())
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1213: in _open
    return open_func(self.baseFilename, self.mode,
E   FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/logs/training.log'
=========================== short test summary info ============================
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_preprocess_housekeeping.py
ERROR tests/unit/test_train.py - FileNotFoundError: [Errno 2] No such file or...
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.94s ===============================


- python -m pytest tests/contract/ -> rc=1
schema.py::TestTssProximityStatsSchema::test_required_keys_present
FAILED tests/contract/test_interpretation_schema.py::TestTssProximityStatsSchema::test_value_types
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_file_exists
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_required_keys_present
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_value_types
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_delta_r2_calculation
ERROR tests/contract/test_data_schema.py::TestSyntheticCountsSchema::test_required_columns_present
ERROR tests/contract/test_data_schema.py::TestSyntheticCountsSchema::test_data_types
ERROR tests/contract/test_data_schema.py::TestSyntheticCountsSchema::test_value_constraints
ERROR tests/contract/test_data_schema.py::TestSyntheticPeaksSchema::test_required_columns_present
ERROR tests/contract/test_data_schema.py::TestSyntheticPeaksSchema::test_data_types
ERROR tests/contract/test_data_schema.py::TestSyntheticPeaksSchema::test_value_constraints
============== 13 failed, 3 passed, 1 skipped, 6 errors in 0.18s ===============


- python -m pytest tests/integration/ -> rc=2
ti/tests/integration/test_training_loop.py _
tests/integration/test_training_loop.py:29: in <module>
    from code.train import train_elastic_net_cv, main as train_main
code/train.py:30: in <module>
    logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'training.log'))
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1181: in __init__
    StreamHandler.__init__(self, self._open())
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1213: in _open
    return open_func(self.baseFilename, self.mode,
E   FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/logs/training.log'
=========================== short test summary info ============================
ERROR tests/integration/test_data_pipeline.py
ERROR tests/integration/test_interpretation.py - FileNotFoundError: [Errno 2]...
ERROR tests/integration/test_training_loop.py - FileNotFoundError: [Errno 2] ...
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.93s ===============================



## Declared deliverables still missing

- data/processed/cell_type_specific_genes.csv
- data/processed/external_validation_r2.csv
- data/processed/housekeeping_genes.csv
- data/processed/housekeeping_matrix.csv
- data/processed/housekeeping_r2.csv
- data/processed/tss_binned_features.csv
- data/raw/checksums.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cell_type_specific_genes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cell_type_specific_genes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_validation_r2.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_validation_r2.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/housekeeping_genes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — NOT invoked by the run-book
    - `code/run_t016.py` — NOT invoked by the run-book
    - `code/run_t016c.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/housekeeping_genes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/housekeeping_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_t016c.py` — NOT invoked by the run-book
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/housekeeping_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/housekeeping_r2.csv` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/housekeeping_r2.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tss_binned_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/run_t016c.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tss_binned_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_encode.py` — IS a run-book command
    - `code/generate_data.py` — NOT invoked by the run-book
    - `code/run_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
