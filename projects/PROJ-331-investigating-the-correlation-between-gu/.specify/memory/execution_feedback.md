# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m code.src.pipeline.ingest (rc=1); python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m pytest -q code/tests (rc=1); 4 declared deliverable(s) absent: data/processed/clr_abundances.parquet; data/processed/filtered_samples.parquet; data/raw/ppmi_asv.csv

## Failing / missing run-book commands

- python -m code.src.pipeline.ingest -> rc=1

2026-10-13 03:03:48,647 INFO __main__: === PPMI input validation (FR-001) ===
2026-10-13 03:03:48,648 ERROR __main__: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.
2026-10-13 03:03:48,648 ERROR __main__: Input validation FAILED: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.

- python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-331-investigating-the-correlation-between-gu/bin/python: No module named code.src.pipeline.__main__; 'code.src.pipeline' is a package and cannot be directly executed

- python -m pytest -q code/tests -> rc=1
 x 150 taxa, ~0.00 GB) within 7 GB budget; no subsampling
------------------------------ Captured log call -------------------------------
INFO     code.src.pipeline.preprocess:preprocess.py:169 Feature set (10 rows x 150 taxa, ~0.00 GB) within 7 GB budget; no subsampling
=========================== short test summary info ============================
FAILED code/tests/test_ingest.py::test_valid_inputs_report_counts_and_outcome
FAILED code/tests/test_ingest.py::test_missing_outcome_column_exits_zero_with_skip_flag
FAILED code/tests/test_ingest.py::test_malformed_asv_missing_columns_aborts
FAILED code/tests/test_ingest.py::test_main_writes_validation_report - Import...
FAILED code/tests/test_preprocess.py::test_single_visit_patients_excluded_with_logged_count
FAILED code/tests/test_preprocess.py::test_two_visit_patients_are_retained - ...
FAILED code/tests/test_preprocess.py::test_zero_taxa_dropped_with_warning - I...
FAILED code/tests/test_preprocess.py::test_clr_output_rows_equal_retained_samples
FAILED code/tests/test_preprocess.py::test_zero_variance_covariate_detected
FAILED code/tests/test_preprocess.py::test_memory_cap_selects_top_taxa - Attr...
10 failed, 3 passed in 1.31s



## Declared deliverables still missing

- data/processed/clr_abundances.parquet
- data/processed/filtered_samples.parquet
- data/raw/ppmi_asv.csv
- data/raw/ppmi_clinical.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clr_abundances.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clr_abundances.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_asv.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_ingest.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_asv.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_clinical.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_ingest.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_clinical.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
