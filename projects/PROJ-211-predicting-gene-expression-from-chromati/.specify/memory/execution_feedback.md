# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_data.py: self-declared fabricated metric — “…tadata fields are filled with placeholder values.     """     # Metadata – pl…”
- code/generate_data.py: self-declared fabricated metric — “…ues.     """     # Metadata – placeholder values sufficient for validation…”
- code/preprocess.py: self-declared fabricated metric — “…errows():             # Use a dummy score of 0 for the BED score column…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the gene e…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…is no silent fallback to synthetic data.  The script can be exec…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…cessibility matrix – for synthetic data we reuse the same consta…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…schema)     logger.info("Synthetic data conforms to the dataset…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…_path)      logger.info("Synthetic data generation completed suc…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/preprocess.py  --counts data/raw/encode_counts.csv  --peaks  data/raw/encode_peaks.bed  --tss    data/raw/gene_coords.bed  --output-dir data/processed`
  - script usage: `preprocess.py [-h]`
  - argparse error: `preprocess.py: error: unrecognized arguments: --counts data/raw/encode_counts.csv --peaks data/raw/encode_peaks.bed --tss data/raw/gene_coords.bed --output-dir data/processed`
- run-book command: `python code/train.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --output-dir data/models`
  - script usage: `train.py [-h] [--input INPUT] [--model-dir MODEL_DIR] [--scores SCORES]`
  - argparse error: `train.py: error: unrecognized arguments: --features data/processed/binned_matrix.csv --targets data/processed/imputed_expression.csv --output-dir data/models`
- run-book command: `python code/train.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --hold-out-cell-line HepG2  --output-dir data/models`
  - script usage: `train.py [-h] [--input INPUT] [--model-dir MODEL_DIR] [--scores SCORES]`
  - argparse error: `train.py: error: unrecognized arguments: --features data/processed/binned_matrix.csv --targets data/processed/imputed_expression.csv --hold-out-cell-line HepG2 --output-dir data/models`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_data.py: self-declared fabricated metric — “…tadata fields are filled with placeholder values.     """     # Metadata – pl…”; code/generate_data.py: self-declared fabricated metric — “…ues.     """     # Metadata – placeholder values sufficient for validation…”; code/preprocess.py: self-declared fabricated metric — “…errows():             # Use a dummy score of 0 for the BED score column…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/generate_synthetic.py --seed 42 --output-dir data/raw; python code/analyze.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --models   data/models  --output-dir data/processed; 7 command(s) failed: python code/download_encode.py  --cell-lines GM128*, K562, HMEC, IMR90, HepG2  --output-dir data/raw (rc=1); python code/preprocess.py  --counts data/raw/encode_counts.csv  --peaks  data/raw/encode_peaks.bed  --tss    data/raw/gene_coords.bed  --output-dir data/processed (rc=2); python code/train.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --output-dir data/models (rc=2); 9 declared deliverable(s) absent: data/processed/cell_type_specific_genes.csv; data/processed/external_validation_r2.csv; data/processed/filtered_expression.csv

## Failing / missing run-book commands

- python code/download_encode.py  --cell-lines GM128*, K562, HMEC, IMR90, HepG2  --output-dir data/raw -> rc=1
2026-10-23 19:15:01,218 - __main__ - INFO - Directories ensured: ['data/raw', 'data/processed', 'data/models', 'logs', 'tests', 'docs', 'contracts']
2026-10-23 19:15:01,652 - __main__ - ERROR - Failed to retrieve ENCODE metadata: RNA-seq file not found for GM12878 after trying all aliases ['GM12878']


- python code/generate_synthetic.py --seed 42 --output-dir data/raw -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-211-predicting-gene-expression-from-chromati/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/generate_synthetic.py': [Errno 2] No such file or directory

- python code/preprocess.py  --counts data/raw/encode_counts.csv  --peaks  data/raw/encode_peaks.bed  --tss    data/raw/gene_coords.bed  --output-dir data/processed -> rc=2

usage: preprocess.py [-h]
preprocess.py: error: unrecognized arguments: --counts data/raw/encode_counts.csv --peaks data/raw/encode_peaks.bed --tss data/raw/gene_coords.bed --output-dir data/processed

- python code/train.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --output-dir data/models -> rc=2

usage: train.py [-h] [--input INPUT] [--model-dir MODEL_DIR] [--scores SCORES]
train.py: error: unrecognized arguments: --features data/processed/binned_matrix.csv --targets data/processed/imputed_expression.csv --output-dir data/models

- python code/train.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --hold-out-cell-line HepG2  --output-dir data/models -> rc=2

usage: train.py [-h] [--input INPUT] [--model-dir MODEL_DIR] [--scores SCORES]
train.py: error: unrecognized arguments: --features data/processed/binned_matrix.csv --targets data/processed/imputed_expression.csv --hold-out-cell-line HepG2 --output-dir data/models

- python code/analyze.py  --features data/processed/binned_matrix.csv  --targets  data/processed/imputed_expression.csv  --models   data/models  --output-dir data/processed -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-211-predicting-gene-expression-from-chromati/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/analyze.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=1
matrix_dimensions
FAILED tests/unit/test_t011_generation.py::TestT011Generation::test_peaks_matrix_dimensions
FAILED tests/unit/test_t011_generation.py::TestT011Generation::test_bed_file_format
FAILED tests/unit/test_t011_generation.py::TestT011Generation::test_reproducibility_with_seed
FAILED tests/unit/test_t011_generation.py::TestT011Generation::test_different_seed_produces_different_data
FAILED tests/unit/test_t011_generation.py::TestT011Generation::test_data_types_in_counts
FAILED tests/unit/test_train.py::TestTrainElasticNet::test_run_cross_validation
FAILED tests/unit/test_train.py::TestTrainElasticNet::test_train_elastic_net
FAILED tests/unit/test_utils.py::TestLoadConfig::test_load_empty_yaml - asser...
ERROR tests/unit/test_preprocess.py::test_bin_aggregation_shape - FileNotFoun...
ERROR tests/unit/test_preprocess.py::test_merge_features_expression - FileNot...
ERROR tests/unit/test_utils.py::TestRetryRequest::test_success_on_first_attempt
ERROR tests/unit/test_utils.py::TestRetryRequest::test_retry_on_failure
ERROR tests/unit/test_utils.py::TestRetryRequest::test_failure_after_max_attempts
============= 25 failed, 33 passed, 3 warnings, 5 errors in 2.40s ==============


- python -m pytest tests/contract/ -> rc=1
nt
FAILED tests/contract/test_interpretation_schema.py::TestFeatureImportanceSchema::test_column_types
FAILED tests/contract/test_interpretation_schema.py::TestPeakAnnotationsSchema::test_file_exists
FAILED tests/contract/test_interpretation_schema.py::TestPeakAnnotationsSchema::test_required_columns_present
FAILED tests/contract/test_interpretation_schema.py::TestPeakAnnotationsSchema::test_column_types
FAILED tests/contract/test_interpretation_schema.py::TestTssProximityStatsSchema::test_file_exists
FAILED tests/contract/test_interpretation_schema.py::TestTssProximityStatsSchema::test_required_keys_present
FAILED tests/contract/test_interpretation_schema.py::TestTssProximityStatsSchema::test_value_types
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_file_exists
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_required_keys_present
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_value_types
FAILED tests/contract/test_interpretation_schema.py::TestPerformanceGapSchema::test_delta_r2_calculation
=================== 15 failed, 1 passed, 7 skipped in 0.28s ====================


- python -m pytest tests/integration/ -> rc=2
/preprocess.py)
_ ERROR collecting projects/PROJ-211-predicting-gene-expression-from-chromati/tests/integration/test_training_loop.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/tests/integration/test_training_loop.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_training_loop.py:29: in <module>
    from code.train import train_elastic_net_cv, main as train_main
E   ImportError: cannot import name 'train_elastic_net_cv' from 'code.train' (/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/train.py)
=========================== short test summary info ============================
ERROR tests/integration/test_data_pipeline.py
ERROR tests/integration/test_training_loop.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.07s ===============================



## Declared deliverables still missing

- data/processed/cell_type_specific_genes.csv
- data/processed/external_validation_r2.csv
- data/processed/filtered_expression.csv
- data/processed/housekeeping_genes.csv
- data/processed/housekeeping_matrix.csv
- data/processed/housekeeping_r2.csv
- data/processed/imputed_binned_features.csv
- data/processed/log_expression.csv
- data/raw/checksums.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cell_type_specific_genes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cell_type_specific_genes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_validation_r2.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_validation_r2.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_expression.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/run_t016c.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_expression.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/housekeeping_genes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
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
- `data/processed/imputed_binned_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/imputed_binned_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/log_expression.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/log_expression.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_encode.py` — IS a run-book command
    - `code/generate_data.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/run_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
