# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): No integration test file or test function for US‑1 acceptance scenario 1 was supplied; the evidence contains no code, file paths, or test definitions, so the required artifact is missing. The next implementer must add a concrete test file (e.g., `tests/integration/test_us1_scenario1.py`) with a function that exercises the pipeline on a 1‑minute Vsw and Ey series and asserts that Pearson and Spearman coefficients and empirical p‑values are returned.
- `T022` (rejected 1x): The claim provides only the specification and acceptance criteria but no actual artifacts (e.g., code, data files, correlation output, plots, or logs) demonstrating that the pipeline cleaned NaN gaps, resampled, and produced the required Pearson/Spearman coefficients without error. Without concrete output or test results, the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

