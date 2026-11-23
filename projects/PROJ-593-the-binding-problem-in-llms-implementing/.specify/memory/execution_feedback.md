# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python src/data/download_plv_reference.py   # creates data/raw/plv_reference.json; python src/benchmarks/clutrr_eval.py --seed 42; python src/benchmarks/babi_eval.py   --seed 42; 4 command(s) failed: python src/main.py  --freq-sweep 30 35 40 45 50  --seeds 42 123 456 789 101  --config config/default.yaml (rc=1); python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/ (rc=2); 7 declared deliverable(s) absent: data/final/control_run_comparison.json; data/final/feature_definition_schema.json; data/final/latency_report.json

## Failing / missing run-book commands

- python src/data/download_plv_reference.py   # creates data/raw/plv_reference.json -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/src/data/download_plv_reference.py': [Errno 2] No such file or directory

- python src/main.py  --freq-sweep 30 35 40 45 50  --seeds 42 123 456 789 101  --config config/default.yaml -> rc=1
src/main.py", line 205, in main
    baseline_wrapper = DistilBERTWrapper(baseline_model)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/code/src/models/base_model.py", line 37, in __init__
    self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/code/.venv/lib/python3.11/site-packages/transformers/tokenization_utils_base.py", line 1590, in from_pretrained
    revision = resolve_revision(
               ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 283, in resolve_revision
    if path_or_repo_id is None or os.path.exists(path_or_repo_id):
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen genericpath>", line 19, in exists
TypeError: stat: path should be string, bytes, os.PathLike or integer, not DistilBERTWrapper

- python src/benchmarks/clutrr_eval.py --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/src/benchmarks/clutrr_eval.py': [Errno 2] No such file or directory

- python src/benchmarks/babi_eval.py   --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/src/benchmarks/babi_eval.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
tems / 1 error

==================================== ERRORS ====================================
___________________ ERROR collecting tests/unit/test_sdc.py ____________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/tests/unit/test_sdc.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_sdc.py:3: in <module>
    from src.analysis.sdc import spectral_density_correlation, compute_sdc_batch
src/analysis/sdc.py:3: in <module>
    from src.analysis.spectral import normalize_psd_to_unit_area
E   ModuleNotFoundError: No module named 'src.analysis.spectral'
=========================== short test summary info ============================
ERROR tests/unit/test_sdc.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 4.33s ===============================


- python -m pytest tests/integration/ -> rc=2
lugins: platformdirs-4.12.4, anyio-4.15.1
collected 0 items / 1 error

==================================== ERRORS ====================================
_________ ERROR collecting tests/integration/test_oscillation_peak.py __________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-593-the-binding-problem-in-llms-implementing/tests/integration/test_oscillation_peak.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_oscillation_peak.py:23: in <module>
    from src.analysis.spectral import compute_fft, calculate_snr
E   ModuleNotFoundError: No module named 'src.analysis.spectral'
=========================== short test summary info ============================
ERROR tests/integration/test_oscillation_peak.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 3.56s ===============================


- python -m pytest tests/contract/ -> rc=1
ept FileNotFoundError:
>           pytest.fail("Spectral features file does not exist. Run T007/T008 preprocessing first.")
E           Failed: Spectral features file does not exist. Run T007/T008 preprocessing first.

tests/contract/test_spectral_features.py:210: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_activation_schema.py::test_activation_schema_structure
FAILED tests/contract/test_clutrr_schema.py::test_clutrr_schema - AssertionEr...
FAILED tests/contract/test_clutrr_schema.py::test_clutrr_data_types - Asserti...
FAILED tests/contract/test_spectral_features.py::test_spectral_features_file_exists
FAILED tests/contract/test_spectral_features.py::test_spectral_features_schema
FAILED tests/contract/test_spectral_features.py::test_spectral_features_data_types
FAILED tests/contract/test_spectral_features.py::test_spectral_features_unit_area_normalization
FAILED tests/contract/test_spectral_features.py::test_spectral_features_band_power_coverage
FAILED tests/contract/test_spectral_features.py::test_spectral_features_peak_detection
========================= 9 failed, 6 passed in 0.37s ==========================



## Declared deliverables still missing

- data/final/control_run_comparison.json
- data/final/feature_definition_schema.json
- data/final/latency_report.json
- data/processed/meg_filtered.npy
- data/processed/meg_psd_normalized.npy
- data/processed/sweep_results.csv
- data/raw/meg_streamed.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/final/control_run_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/control_run.py` — NOT invoked by the run-book
    - `code/src/analysis/layer_metrics.py` — NOT invoked by the run-book
    - `code/src/analysis/snr_verification.py` — NOT invoked by the run-book
    - `code/tests/integration/test_control_run.py` — NOT invoked by the run-book
    - `code/tests/unit/test_layer_metrics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_snr_verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/control_run_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/feature_definition_schema.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_feature_definition_schema.py` — NOT invoked by the run-book
    - `code/src/models/feature_definition.py` — NOT invoked by the run-book
    - `code/tests/unit/test_feature_definition.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/feature_definition_schema.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/latency_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/latency_monitor.py` — NOT invoked by the run-book
    - `code/tests/unit/test_latency_monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/latency_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/meg_filtered.npy` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/preprocess_meg.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_meg_part2.py` — NOT invoked by the run-book
    - `src/data/preprocess_meg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/meg_filtered.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/meg_psd_normalized.npy` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/layer_metrics.py` — NOT invoked by the run-book
    - `code/src/data/preprocess_meg.py` — NOT invoked by the run-book
    - `src/data/preprocess_meg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/meg_psd_normalized.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sweep_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
    - `src/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sweep_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/meg_streamed.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download_meg.py` — NOT invoked by the run-book
    - `code/src/data/preprocess_meg.py` — NOT invoked by the run-book
    - `code/tests/unit/test_download_meg.py` — NOT invoked by the run-book
    - `code/tests/unit/test_preprocess_meg.py` — NOT invoked by the run-book
    - `src/data/download_meg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/meg_streamed.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
