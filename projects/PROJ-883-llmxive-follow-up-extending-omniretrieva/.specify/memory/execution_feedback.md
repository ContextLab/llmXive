# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/execution_logs.csv, data/processed/generation_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/execution_logs.csv, data/processed/generation_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 command(s) failed: python -m pytest -v (rc=1)

## Failing / missing run-book commands

- python -m pytest -v -> rc=1
tional argument: 'levels'
FAILED tests/unit/test_synthetic_query.py::TestSyntheticQueryGenerator::test_generate_queries_complexity_levels - TypeError: SyntheticQueryGenerator.__init__() missing 1 required positional argument: 'levels'
FAILED tests/unit/test_synthetic_query.py::TestSyntheticQueryGenerator::test_save_queries_creates_file - TypeError: SyntheticQueryGenerator.__init__() missing 1 required positional argument: 'levels'
FAILED tests/unit/test_synthetic_query.py::TestSyntheticQueryGenerator::test_ground_truth_plan_determinism - TypeError: SyntheticQueryGenerator.__init__() missing 1 required positional argument: 'levels'
FAILED tests/unit/test_validate_schemas.py::test_query_instance_schema - jsonschema.exceptions.ValidationError: query_instance does not conform to its schema.
FAILED tests/unit/test_validate_schemas.py::test_execution_log_schema - jsonschema.exceptions.ValidationError: execution_log does not conform to its schema.
FAILED tests/unit/test_validate_schemas.py::test_execution_metric_schema - jsonschema.exceptions.ValidationError: execution_metric does not conform to its schema.
=================== 26 failed, 52 passed, 1 skipped in 1.05s ===================


