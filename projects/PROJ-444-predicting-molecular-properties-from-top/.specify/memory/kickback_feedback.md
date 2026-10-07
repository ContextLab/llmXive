# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): The required output files `data/checksums.txt` and `state/projects/PROJ-444-predicting-molecular-properties-from-top.yaml` are absent, so the script’s effects cannot be verified. Additionally, the provided `code/00_checksum_verify.py` is truncated and does not show the full implementation (e.g., completing the state update, handling empty `data/raw/`, or invoking the checksum computation). The task therefore remains unfinished.
- `T008b` (rejected 1x): The repository contains `code/01_data_ingestion.py`, but the file is truncated and does not show any implementation of scaffold counting, the ≥100 scaffold check, or the 5‑fold Murcko scaffold split. Moreover, the required output artifacts `data/processed/scaffold_counts.json` and `data/processed/splits.json` are absent from the project. Without these files and the corresponding logic, the task’s deliverables are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

