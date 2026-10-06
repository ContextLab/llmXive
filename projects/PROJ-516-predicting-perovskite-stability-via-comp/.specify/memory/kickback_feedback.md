# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/nrel_perovskites.csv, data/raw/mp_perovskites.csv
- `T012e` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/perovskites_merged.csv
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/metadata.json, schema.yaml
- `T014c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors_features.csv
- `T016a` (rejected 1x): The repository lacks the required `data/processed/descriptors_v1.csv` input file and the `data/processed/vif_report.csv` output file, so the script cannot be run or verified. Moreover, the provided `vif_calculator.py` is truncated and does not contain the logic to write the CSV with the specified columns (`descriptor`, `vif_value`, `flagged`). The task therefore remains unfinished.
- `T015a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors_vif_filtered.csv, data/processed/descriptors_final_filtered.csv, data/processed/exclusion_log.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

