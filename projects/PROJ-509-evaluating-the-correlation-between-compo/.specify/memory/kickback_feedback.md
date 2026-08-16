# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T049a` (rejected 1x): No evidence was provided that `autoflake --in-place --remove-all-unused-imports code/` was executed, nor any before‑and‑after view of the `code/utils/` files showing unused imports removed. The required artifact (the refactored code without unused imports) is missing.
- `T049b` (rejected 1x): No artifact (e.g., a formatted code snapshot, a Black report, or a commit showing the `code/` directory with line lengths ≤ 88) was provided, so we cannot confirm that `black --line-length 88 code/` was actually executed and succeeded. The implementer must supply evidence that the `code/` files have been reformatted to meet the line‑length constraint.
- `T051` (rejected 1x): No evidence of any new unit test files or test cases under `tests/unit/` was provided; the claim of “additional unit tests for edge cases (missing elements, extreme outliers)” cannot be verified. The required test artifacts are missing.
- `T052` (rejected 1x): No evidence of a `quickstart.md` validation run, logs, or reproducibility report is present; the required artifact confirming end‑to‑end execution is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

