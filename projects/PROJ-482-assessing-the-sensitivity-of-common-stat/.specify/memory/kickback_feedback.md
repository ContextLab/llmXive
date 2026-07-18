# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017b` (rejected 1x): No log entry or any other artifact confirming that the ground‑truth validation routine from T013 was executed and passed (exit code 0) is present. The required evidence—a non‑empty log confirming verification of the current configuration batch—is missing, so the task is not satisfied.
- `T021b` (rejected 1x): The `data/processed/raw_pvalues.csv` file contains only the header line and no p‑value rows, indicating that raw p‑values are not being streamed or stored. The provided `code/simulation_engine.py` excerpt shows test execution functions but no logic that writes p‑values to the CSV (or streams them in real‑time). Consequently, the required functionality is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

