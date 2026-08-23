# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/load_nist.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/load_pubchem.py
- `T013` (rejected 1x): No code changes or files were presented for `src/ingestion/load_*.py`; thus there is no evidence that provenance‑filtering logic was added or that any fallback mechanism was removed. The required artifact (the updated ingestion scripts) is missing.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/merge_spectra.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

