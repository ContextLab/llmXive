# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018e` (rejected 1x): The provided `code/ingestion.py` does not contain an implementation of `fetch_arxiv_supplementary_data()` (the snippet shows only helper utilities), and the required output file `data/raw/arxiv_raw.json` is absent. Consequently the task’s core functionality and output artifact are missing.
- `T017b` (rejected 1x): The repository lacks `data/processed/final_count.txt`, `data/reports/data_availability_report.json`, and the required `data/raw/test_n.csv`. The `validate_data_gap()` function is not present (or not fully implemented) in `code/ingestion.py`, and the unit test confirming exit code 1 for N < 30 is absent. These missing artifacts prevent the task from being considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

