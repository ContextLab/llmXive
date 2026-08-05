# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001b` (rejected 1x): No actual `__init__.py` files were presented for any of the required directories; the evidence consists only of a claim without any file listings or contents. The required artifacts are missing, so the task is not satisfied.
- `T001c` (rejected 1x): No evidence of `.gitkeep` files was presented for any of the required directories (`data/raw/`, `data/processed/`, `data/results/`, `artifacts/synthesized_adapters/`, `specs/001-lattentskill-retrieval-geometry/contracts/`). Without these files present, the task requirement is not satisfied. The implementer must add a `.gitkeep` file to each listed path.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

