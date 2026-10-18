# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/cochrane_base_synthetic.csv, data/results/estimation_results.csv, data/results/reml_failures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode dry-run --replicates-per-level 10 --tau-values 0 0.1 --seed 42`
  - script usage: `main.py [-h] [--mode {full,dry-run}] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --replicates-per-level 10 --tau-values 0 0.1`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/cochrane_base_synthetic.csv, data/results/estimation_results.csv, data/results/reml_failures.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/scripts/fetch_openml.py   # downloads to data/raw/openml_4210.csv (rc=1); python code/main.py --mode dry-run --replicates-per-level 10 --tau-values 0 0.1 --seed 42 (rc=2); python -m pytest tests/unit/ (rc=1); 5 declared deliverable(s) absent: data/raw/cochrane_base.csv; data/results/aggregated_metrics.csv; data/results/coverage_vs_tau2.png

## Failing / missing run-book commands

- python code/scripts/fetch_openml.py   # downloads to data/raw/openml_4210.csv -> rc=1
============================================================
FETCHING OPENML DATASET
============================================================
Fetching OpenML dataset ID 4210 ...
============================================================

ERROR: REAL_DATA_FETCH_FAILED: unable to retrieve OpenML metadata for dataset 4210: HTTP Error 412: Precondition Failed

- python code/main.py --mode dry-run --replicates-per-level 10 --tau-values 0 0.1 --seed 42 -> rc=2

usage: main.py [-h] [--mode {full,dry-run}] [--seed SEED]
               [--levels LEVELS [LEVELS ...]] [--replicates REPLICATES]
               [--base-data BASE_DATA] [--skip-generation]
               [--validate-contracts] [--verbose]
main.py: error: unrecognized arguments: --replicates-per-level 10 --tau-values 0 0.1

- python -m pytest tests/unit/ -> rc=1
unit/test_config_loader.py::TestGetReplicateCount::test_get_replicate_count_sensitivity
FAILED tests/unit/test_config_loader.py::TestGetReplicateCount::test_get_replicate_count_default
FAILED tests/unit/test_estimators.py::TestREML::test_failure_logging_and_fallback
FAILED tests/unit/test_plots.py::test_plots_generate_files - SystemExit: 1
FAILED tests/unit/test_reml_failure_log.py::test_log_reml_failure_appends_events
FAILED tests/unit/test_stats.py::test_conditional_test_non_normal_data - Asse...
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_invalid_record_missing_field
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_invalid_record_wrong_type
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_save_dummy_record_to_results
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_schema_file_exists
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_schema_has_required_fields
ERROR tests/unit/test_schema_validation.py::TestEstimationResultSchema::test_valid_record_conforms
============= 12 failed, 65 passed, 13 warnings, 6 errors in 1.49s =============


- python -m pytest tests/integration/ -> rc=1
            +    where <bound method Path.is_file of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/data/results/stability_analysis.json')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/data/results/stability_analysis.json').is_file

tests/integration/test_pipeline.py:59: AssertionError
=============================== warnings summary ===============================
tests/integration/test_pipeline.py:30
  /home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/integration/test_pipeline.py:30: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_pipeline.py::test_full_pipeline_dry_run - Asser...
========================= 1 failed, 1 warning in 0.42s =========================



## Declared deliverables still missing

- data/raw/cochrane_base.csv
- data/results/aggregated_metrics.csv
- data/results/coverage_vs_tau2.png
- data/results/mean_bias_vs_tau2.png
- data/results/stability_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/cochrane_base.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config_loader.py` — NOT invoked by the run-book
    - `code/fetch_cochrane_data.py` — NOT invoked by the run-book
    - `code/generate_synthetic_base.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/adapt_parameters.py` — NOT invoked by the run-book
    - `code/scripts/fetch_cochrane.py` — NOT invoked by the run-book
    - `code/scripts/fetch_openml.py` — IS a run-book command
    - `code/scripts/generate_synthetic_base.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/cochrane_base.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_aggregated_metrics.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/coverage_vs_tau2.png` is declared but was NOT written. Scripts referencing it:
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/coverage_vs_tau2.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mean_bias_vs_tau2.png` is declared but was NOT written. Scripts referencing it:
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mean_bias_vs_tau2.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
