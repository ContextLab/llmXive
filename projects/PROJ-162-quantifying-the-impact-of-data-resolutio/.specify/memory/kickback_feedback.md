# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file list showing the required folders (`src`, `tests`, `data/raw`, `data/processed`, `data/profiling`, `contracts`, `state`) was provided; therefore the claimed creation of the project structure cannot be verified. The implementer must supply evidence (e.g., a directory listing or screenshots) that these directories exist and are non‑empty where appropriate.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_hygiene.py
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_hygiene.py
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/profiler.py, data/profiling/memory_error.log
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/downsample.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

