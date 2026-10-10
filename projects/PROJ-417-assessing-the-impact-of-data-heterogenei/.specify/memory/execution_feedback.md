# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/cochrane_base_synthetic.csv, data/results/estimation_results.csv, data/results/reml_failures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/cochrane_base_synthetic.csv, data/results/estimation_results.csv, data/results/reml_failures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 command(s) failed: python -m pytest tests/unit/ (rc=1); 1 declared deliverable(s) absent: data/raw/cochrane_base.csv

## Failing / missing run-book commands

- python -m pytest tests/unit/ -> rc=1
schema.py::test_schema_rejects_invalid_record
FAILED tests/unit/test_config_loader.py::TestGetReplicateCount::test_get_replicate_count_primary
FAILED tests/unit/test_config_loader.py::TestGetReplicateCount::test_get_replicate_count_sensitivity
FAILED tests/unit/test_config_loader.py::TestGetReplicateCount::test_get_replicate_count_default
FAILED tests/unit/test_estimators.py::TestREML::test_failure_logging_and_fallback
FAILED tests/unit/test_project_structure.py::test_init_files_exist - Assertio...
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_invalid_record_missing_field
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_invalid_record_wrong_type
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_save_dummy_record_to_results
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_schema_file_exists
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_schema_has_required_fields
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_valid_record_conforms
=================== 10 failed, 74 passed, 6 errors in 1.29s ====================



## Declared deliverables still missing

- data/raw/cochrane_base.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/cochrane_base.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config_loader.py` — NOT invoked by the run-book
    - `code/fetch_cochrane_data.py` — NOT invoked by the run-book
    - `code/generate_synthetic_base.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/adapt_parameters.py` — NOT invoked by the run-book
    - `code/scripts/fetch_cochrane.py` — IS a run-book command
    - `code/scripts/generate_synthetic_base.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/cochrane_base.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
