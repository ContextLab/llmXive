# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m code.src.pipeline.ingest (rc=1); python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m code.src.pipeline.run_us3 --iterations 1000 --seed 42 (rc=1); 10 declared deliverable(s) absent: data/processed/clr_abundances.parquet; data/processed/filtered_samples.parquet; data/processed/patient_outcome_slopes.parquet

## Failing / missing run-book commands

- python -m code.src.pipeline.ingest -> rc=1

2026-10-13 10:11:42,702 INFO __main__: === PPMI input validation (FR-001) ===
2026-10-13 10:11:42,702 ERROR __main__: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv exist. Place the researcher‑supplied asv table at one of these locations.
2026-10-13 10:11:42,702 ERROR __main__: Input validation FAILED: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv exist. Place the researcher‑supplied asv table at one of these locations.

- python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 -> rc=1
^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 262, in main
    report = validate_inputs(asv_path, clinical_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 198, in validate_inputs
    asv_path = _choose_path(
               ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 81, in _choose_path
    _fail(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 52, in _fail
    raise FileNotFoundError(message)
FileNotFoundError: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv exist. Place the researcher‑supplied asv table at one of these locations.

- python -m code.src.pipeline.run_us3 --iterations 1000 --seed 42 -> rc=1
^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 262, in main
    report = validate_inputs(asv_path, clinical_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 198, in validate_inputs
    asv_path = _choose_path(
               ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 81, in _choose_path
    _fail(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 52, in _fail
    raise FileNotFoundError(message)
FileNotFoundError: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv exist. Place the researcher‑supplied asv table at one of these locations.

- python -m pytest -q code/tests -> rc=1
mple - ImportEr...
FAILED code/tests/test_slopes.py::test_two_visit_patients_included_single_visit_excluded
FAILED code/tests/test_slopes.py::test_constant_outcome_yields_zero_slope - I...
FAILED code/tests/test_slopes.py::test_compute_outcome_slopes_simple - Import...
FAILED code/tests/test_slopes.py::test_run_slopes_writes_files - ImportError:...
FAILED code/tests/test_slopes.py::test_run_slopes_missing_outcome - ImportErr...
ERROR code/tests/contract/test_contracts.py::test_taxa_correlations_contract
ERROR code/tests/test_correlation.py::test_correlation_produces_results - Imp...
ERROR code/tests/test_mixed_effects.py::test_mixed_effects_recovers_known_interaction
ERROR code/tests/test_mixed_effects.py::test_missing_outcome_causes_empty_file
ERROR code/tests/test_permutation.py::test_permutation_runs - ImportError: Un...
ERROR code/tests/test_runtime_budget.py::test_runtime_logging_and_budget - At...
ERROR code/tests/test_verify_dataset.py::test_successful_verification - Impor...
ERROR code/tests/test_verify_dataset.py::test_checksum_mismatch_raises - Impo...
ERROR code/tests/test_verify_dataset.py::test_unreachable_citation_raises - I...
16 failed, 5 passed, 9 errors in 4.56s



## Declared deliverables still missing

- data/processed/clr_abundances.parquet
- data/processed/filtered_samples.parquet
- data/processed/patient_outcome_slopes.parquet
- data/processed/patient_taxon_slopes.parquet
- data/raw/ppmi_asv.csv
- data/raw/ppmi_clinical.parquet
- data/results/mixed_effects_summary.csv
- data/results/partial_spearman_exploratory.csv
- data/results/permutation_pvalues.csv
- data/results/taxa_correlations.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clr_abundances.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_mixed_effects.py` — NOT invoked by the run-book
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clr_abundances.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_outcome_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_outcome_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_taxon_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_taxon_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_asv.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/verify_dataset.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_ingest.py` — NOT invoked by the run-book
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_asv.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_clinical.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
    - `code/src/pipeline/verify_dataset.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_clinical.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mixed_effects_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us3.py` — IS a run-book command
    - `code/tests/test_mixed_effects.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mixed_effects_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/partial_spearman_exploratory.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/partial_spearman_exploratory.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us3.py` — IS a run-book command
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/taxa_correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/taxa_correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
