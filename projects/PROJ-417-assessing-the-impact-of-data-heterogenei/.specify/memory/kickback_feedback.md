# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The repository lacks the required `contracts/simulated_dataset.schema.yaml` file, so the generator cannot be verified to produce schema‑conforming output. Moreover, the provided `generator.py` is incomplete (truncated) and does not show a loop that creates ≥500 replicates for each heterogeneity level nor writes results with the required `injected_true_effect` and `injected_tau2` columns. Both the schema and full implementation are missing.
- `T012` (rejected 1x): No `generator.py` file or code snippet was provided, and there is no evidence that any logic handling the τ² = 0 edge case was added. Without the actual implementation (or a description of the changes) we cannot confirm the required functionality exists. The next implementer must supply the updated `generator.py` showing the zero‑variance handling logic.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

