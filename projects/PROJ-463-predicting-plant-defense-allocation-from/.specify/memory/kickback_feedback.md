# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011a` (rejected 1x): The repository contains `src/data/verify_metadata.py`, but the file is truncated and there is no `data/processed/metadata_verification_report.json` generated (the file is missing). Without the required output report (and with an incomplete script), the task’s specification is not satisfied.
- `T013` (rejected 1x): The provided `src/data/batch_correction.py` does not write the required `data/manifests/batch_correction_report.json` (the file is missing) and lacks a proper ComBat‑seq implementation, does not use `scipy.stats` for the GeNorm M‑value, and does not compute and record the pre‑ and post‑correction CV reduction as specified. The task therefore remains unfinished.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/post_qc_species_list.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

