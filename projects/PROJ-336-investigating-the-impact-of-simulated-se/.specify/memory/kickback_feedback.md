# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`src/`, `tests/`, `data/`, `results/`) is presented; the implementer did not supply a directory listing or any files showing that the project structure has been created.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/config.py
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/atlas.py
- `T006` (rejected 1x): The required file `src/data/quality_check.py` is missing entirely, so no code, exclusion manifest, logging, or error‑handling exists to meet the specification. The task cannot be considered done until this file is created with the described functionality.
- `T007` (rejected 1x): No `main.py` file or any code implementing the required orchestration, checkpointing, and resumption logic was provided; the evidence section contains no artifacts to verify. The task therefore remains unfulfilled.
- `T008` (rejected 1x): No evidence of a modified `main.py` implementing disk‑quota enforcement, compression of intermediate files, or checkpointing is provided; the required artifact is missing, so the task cannot be confirmed as completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

