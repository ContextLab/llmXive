# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T049a` (rejected 1x): No code artifacts, diff, or commit showing that `code/utils/` has been examined and unused imports removed are provided. Without any files or evidence of the refactor, the requirement cannot be verified as satisfied. The implementer must supply the updated `code/utils/` files (or a patch/diff) demonstrating that all unused imports have been eliminated.
- `T049b` (rejected 1x): No code artifacts from the `code/` directory are provided, and there is no evidence (e.g., a diff, linter report, or updated files) showing that line lengths have been limited to < 88 characters. Without the actual refactored source files or a verification report, the requirement cannot be confirmed.
- `T051` (rejected 1x): No evidence of any new unit test files or test cases under `tests/unit/` was provided; the claim of “additional unit tests for edge cases (missing elements, extreme outliers)” cannot be verified because the required test artifacts are missing. The next implementer must add concrete test files (e.g., `test_missing_elements.py`, `test_extreme_outliers.py`) that exercise the relevant functions and ensure they are present and non‑empty.
- `T052` (rejected 1x): No artifacts such as a `quickstart.md` file, execution logs, or reproducibility reports are present to demonstrate that the quickstart validation was actually run. Consequently, there is no evidence that the end‑to‑end pipeline was executed and verified as required.
- `T053` (rejected 1x): No `research.md` file is present, and there is no evidence of a summary containing the required metrics, VIF results, and ALE interpretations. The task’s deliverable is missing entirely.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

