# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010a` (rejected 1x): The provided `code/01_data_acquisition.py` does not show any implementation of the Materials Project API query or exponential‑backoff retry logic, and the generated `data/raw/pristine_structures.csv` contains only the header (no structures). Consequently there is no evidence that ≥50 pristine graphene/MoS₂ structures were retrieved, nor that the required backoff mechanism was implemented. The task’s core functional requirement is therefore unmet.
- `T010b` (rejected 1x): The provided `code/01_data_acquisition.py` does not contain any logic that checks for API failure, loads `data/raw/pristine_structures.csv`, validates it, or writes `data/state/cache_load_log.json`. Moreover, the required output file `data/state/cache_load_log.json` is absent, and the cache CSV contains only a header (no valid data). The cache‑fallback step is therefore not implemented nor demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

