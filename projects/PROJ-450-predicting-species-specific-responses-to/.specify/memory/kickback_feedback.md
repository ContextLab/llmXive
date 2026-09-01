# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_us2_regression.R
- `T023a` (rejected 1x): The provided `src/code/analyze_shifts.R` file is present but the shown code stops before any regression results are calculated, confidence intervals extracted, or CSV/plot files written, so we cannot confirm it produces the required slope, 95 % CI, R², p‑value, and per‑region summary outputs. The script also never reaches the WLS fallback because the phylogeny file is missing, but the essential result‑generation logic is absent. The implementation must be completed to compute and export the specified statistics and regional summaries.
- `T027` (rejected 1x): No code files, log files, or other artifacts (e.g., modified `analyze_shifts.R` or `plotting.R` with added logging, generated logs, or regression output) were presented. Without any tangible files to inspect, we cannot verify that logging was added as required. The implementer must supply the updated R scripts and example log/output files demonstrating the recorded regression steps, per‑region results, and plot generation details.
- `T035` (rejected 1x): No test results, logs, or any evidence of a `testthat` suite execution were supplied; the implementer did not provide the required artifact (e.g., a test report, console output, or CI badge) demonstrating that all unit and integration tests were actually run. Consequently the claim cannot be verified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

