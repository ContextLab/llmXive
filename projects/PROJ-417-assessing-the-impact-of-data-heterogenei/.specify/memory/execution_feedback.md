# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- results/reml_failures.json: results file is EMPTY ([]) — the analysis produced no values

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: results/reml_failures.json: results file is EMPTY ([]) — the analysis produced no values; 2 command(s) failed: python -m pytest tests/unit/ (rc=1); python -m pytest tests/integration/ (rc=1); 2 declared deliverable(s) absent: data/results/aggregated_metrics.csv; data/results/reml_failures.json

## Failing / missing run-book commands

- python -m pytest tests/unit/ -> rc=1
uccessful_run - ass...
FAILED tests/unit/test_main.py::test_main_dry_run_creates_outputs - Assertion...
FAILED tests/unit/test_metrics.py::test_compute_metrics_strict_column_check
FAILED tests/unit/test_plots.py::test_plots_generate_files - AssertionError: ...
FAILED tests/unit/test_stats.py::test_conditional_test_normal_data - Assertio...
FAILED tests/unit/test_stats.py::test_conditional_test_non_normal_data - Asse...
FAILED tests/unit/test_validate_cochrane_csv.py::test_validate_success - File...
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_invalid_record_missing_field
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_invalid_record_wrong_type
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_save_dummy_record_to_results
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_schema_file_exists
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_schema_has_required_fields
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_valid_record_conforms
============ 17 failed, 69 passed, 204 warnings, 6 errors in 3.07s =============


- python -m pytest tests/integration/ -> rc=1

E            +    where <bound method Path.is_file of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/data/results/estimation_results.csv')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/data/results/estimation_results.csv').is_file

tests/integration/test_pipeline.py:58: AssertionError
=============================== warnings summary ===============================
tests/integration/test_pipeline.py:30
  /home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/integration/test_pipeline.py:30: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_pipeline.py::test_full_pipeline_dry_run - Asser...
========================= 1 failed, 1 warning in 1.11s =========================



## Declared deliverables still missing

- data/results/aggregated_metrics.csv
- data/results/reml_failures.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_aggregated_metrics.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/reml_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/simulation/estimators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/reml_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
