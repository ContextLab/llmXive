# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The repository contains the required script, participants file, trial‑level CSVs, and compliance‑log directory, but there is no inspected evidence that `data/raw/simulated_measurements.csv` actually contains scored records that conform to `contracts/dataset.schema.yaml`, nor that `data/checksums.sha256` includes correct SHA‑256 entries, nor that `data/results/smoke_results.json` was generated with the expected mean‑change values. Without proof that these outputs exist and meet the schema and checksum requirements, the task’s deliverables are not fully verified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

