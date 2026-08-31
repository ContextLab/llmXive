# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The provided `code/download.py` is truncated and does not contain the full logic for fetching datasets, computing/verifying checksums, generating missing hashes, filtering for required columns, logging exclusions, or updating `README.md`. Moreover, the README lists a dataset (42278) that is not present in `dataset_ids.txt`, and no checksum information is recorded. These gaps mean the task’s requirements are not genuinely fulfilled.
- `T013` (rejected 1x): The `code/update_readme.py` file is present but the shown excerpt stops before any code that writes to `data/README.md`; no function that updates the README based on the exclusion log is visible. Moreover, `data/processed/exclusion_log.json` is empty (`[]`), so there are no exclusion reasons to demonstrate that the script correctly adds them to the README. The required behavior of reading the log and updating the README with statuses/reasons is not evidenced.
- `T014a` (rejected 1x): The claim provides no downloadable scripts, no processed CSV files, and no documentation (README, logs) required by User Story 1. There is no evidence of dataset retrieval, filtering, surprisal computation, or the ≥100‑row output, so the core deliverable is missing.
- `T014b` (rejected 1x): No download or preprocessing scripts, no generated CSV files, and no exclusion‑logging documentation are present. The required artifacts (code to fetch datasets, compute surprisal, produce standardized CSVs with ≥100 rows, and log exclusions) are missing, so the task’s mandatory user story is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

