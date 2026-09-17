# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): The submission contains no code defining SHA256 checksum utilities, nor a generated `artifacts/checksums.txt` listing checksums for the files in `data/`. Without these artifacts, the task requirement is not satisfied.
- `T012` (rejected 1x): The repository contains `code/preprocess_microbiome.py`, but the script is truncated and does not show the required QIIME2 processing, pseudocount application, or checksum handling, and the expected output file `data/processed/microbiome_features.csv` is absent. Without the CSV being generated, the task’s core requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

