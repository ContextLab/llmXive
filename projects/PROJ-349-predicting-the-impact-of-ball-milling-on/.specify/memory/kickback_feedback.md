# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository contains `src/ingest/materials_project.py`, but the implementation is truncated and does not show a complete fetch‑parse‑write workflow, and the required output file `data/raw/materials_project_raw.json` is absent. Without the JSON file (and with an incomplete script), the task’s verification condition of a non‑empty output file is not met. The next implementer must finish the fetcher logic and ensure the JSON file is created (or correctly logged/skipped) as specified.
- `T013` (rejected 1x): The repository contains a partially shown `src/ingest/nist_repo.py`, but the required fallback CSV (`data/fallback/uci_verified_subset.csv`), the output CSV (`data/raw/nist_milling_data.csv`), and the schema file (`contracts/dataset.schema.yaml`) are all absent. Consequently the downloader cannot fulfill the fallback or output requirements, and the verification step cannot be satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

