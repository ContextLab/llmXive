# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018b` (rejected 1x): The `variance_scaling.py` file does not contain any code that writes the derived expression to a JSON file, and the file is truncated (e.g., the `verify_symmetry_and_linearity` function is incomplete). Moreover, the required `src/derivation/sample_complexity.py` file is completely missing, so there is no code that loads the exported JSON. Both required artifacts are absent or incomplete.
- `T019a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/derivation/sample_complexity.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

