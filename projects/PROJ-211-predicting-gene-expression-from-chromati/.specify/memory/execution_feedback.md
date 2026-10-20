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

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/GM12878_binned_features.csv, data/processed/GM12878_imputed_binned_features.csv, data/processed/HMEC_binned_features.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_data.py: self-declared fabricated metric — “…tadata fields are filled with placeholder values.     """     # Metadata – pl…”; code/generate_data.py: self-declared fabricated metric — “…ues.     """     # Metadata – placeholder values sufficient for validation…”; code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the gene e…”; every produced artifact is gitignored (data/processed/GM12878_binned_features.csv, data/processed/GM12878_imputed_binned_features.csv, data/processed/HMEC_binned_features.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/analyze.py; 5 command(s) failed: python code/preprocess.py (rc=1); python code/train.py (rc=1); python -m pytest tests/unit/ (rc=2); 7 declared deliverable(s) absent: data/processed/cell_type_specific_genes.csv; data/processed/external_validation_r2.csv; data/processed/housekeeping_genes.csv

## Failing / missing run-book commands

- python code/preprocess.py -> rc=1
ad, to perform the operation inplace on the original object.


  imputed[col].fillna(median_val, inplace=True)
/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/preprocess.py:220: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  imputed[col].fillna(median_val, inplace=True)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/preprocess.py", line 339, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/preprocess.py", line 329, in main
    writer = csv.writer(fh)
             ^^^
NameError: name 'csv' is not defined

- python code/train.py -> rc=1
2026-10-20 19:15:37,128 - INFO - Starting training pipeline for data/processed/imputed_expression.csv
2026-10-20 19:15:37,128 - INFO - Loading data from data/processed/imputed_expression.csv
2026-10-20 19:15:37,128 - ERROR - Failed to load data: [Errno 2] No such file or directory: 'data/processed/imputed_expression.csv'
2026-10-20 19:15:37,128 - ERROR - Training failed: [Errno 2] No such file or directory: 'data/processed/imputed_expression.csv'


- python code/analyze.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-211-predicting-gene-expression-from-chromati/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/analyze.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
======== ERRORS ====================================
_ ERROR collecting projects/PROJ-211-predicting-gene-expression-from-chromati/tests/unit/test_preprocess_housekeeping.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/tests/unit/test_preprocess_housekeeping.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_preprocess_housekeeping.py:13: in <module>
    from preprocess import (
E   ImportError: cannot import name 'calculate_coefficient_of_variation' from 'preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/tests/unit/../../code/preprocess.py)
=========================== short test summary info ============================
ERROR tests/unit/test_preprocess_housekeeping.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.08s ===============================


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
=================== 15 failed, 1 passed, 7 skipped in 0.24s ====================


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
============================== 2 errors in 1.02s ===============================



## Declared deliverables still missing

- data/processed/cell_type_specific_genes.csv
- data/processed/external_validation_r2.csv
- data/processed/housekeeping_genes.csv
- data/processed/housekeeping_matrix.csv
- data/processed/housekeeping_r2.csv
- data/processed/tss_binned_features.csv
- data/raw/synthetic_counts.csv

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
    - `code/run_t016c.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tss_binned_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_counts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_data.py` — NOT invoked by the run-book
    - `code/run_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_counts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
