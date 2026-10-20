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

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_data.py: self-declared fabricated metric — “…tadata fields are filled with placeholder values.     """     # Metadata – pl…”; code/generate_data.py: self-declared fabricated metric — “…ues.     """     # Metadata – placeholder values sufficient for validation…”; code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the gene e…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/analyze.py; 6 command(s) failed: python code/download_encode.py --cell-lines GM12878,K562,HMEC,IMR90,HepG2 (rc=1); python code/preprocess.py (rc=1); python code/train.py (rc=1); 11 declared deliverable(s) absent: data/processed/cell_type_specific_genes.csv; data/processed/external_validation_r2.csv; data/processed/filtered_expression.csv

## Failing / missing run-book commands

- python code/download_encode.py --cell-lines GM12878,K562,HMEC,IMR90,HepG2 -> rc=1
redicting-gene-expression-from-chromati/code/download_encode.py", line 360, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/download_encode.py", line 314, in main
    metadata = fetch_encode_metadata(cell_lines, session)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/download_encode.py", line 119, in fetch_encode_metadata
    rna_uri = _query_encode_file(
              ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/download_encode.py", line 99, in _query_encode_file
    resp.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://www.encodeproject.org/search/?type=File&assay_title=RNA-seq&biosample_ontology.term_name=GM12878&output_type=gene+quantifications&status=released&limit=1&field=href&file_format=tsv

- python code/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/preprocess.py", line 339, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/preprocess.py", line 284, in main
    gene_coords = load_gene_coords()
                  ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-211-predicting-gene-expression-from-chromati/code/preprocess.py", line 83, in load_gene_coords
    raise FileNotFoundError(f"Gene coordinates file not found: {path}")
FileNotFoundError: Gene coordinates file not found: data/raw/gene_coords.bed

- python code/train.py -> rc=1
2026-10-20 21:08:37,511 - INFO - Starting training pipeline for data/processed/imputed_expression.csv
2026-10-20 21:08:37,511 - INFO - Loading data from data/processed/imputed_expression.csv
2026-10-20 21:08:37,511 - ERROR - Failed to load data: [Errno 2] No such file or directory: 'data/processed/imputed_expression.csv'
2026-10-20 21:08:37,511 - ERROR - Training failed: [Errno 2] No such file or directory: 'data/processed/imputed_expression.csv'


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
=============================== 1 error in 1.11s ===============================


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
============================== 2 errors in 1.06s ===============================



## Declared deliverables still missing

- data/processed/cell_type_specific_genes.csv
- data/processed/external_validation_r2.csv
- data/processed/filtered_expression.csv
- data/processed/housekeeping_genes.csv
- data/processed/housekeeping_matrix.csv
- data/processed/housekeeping_r2.csv
- data/processed/imputed_binned_features.csv
- data/processed/log_expression.csv
- data/processed/tss_binned_features.csv
- data/raw/checksums.csv
- data/raw/synthetic_counts.csv

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
- `data/processed/tss_binned_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
    - `code/run_t016c.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tss_binned_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_encode.py` — IS a run-book command
    - `code/generate_data.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
    - `code/run_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_counts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_data.py` — NOT invoked by the run-book
    - `code/run_t011.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_counts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
