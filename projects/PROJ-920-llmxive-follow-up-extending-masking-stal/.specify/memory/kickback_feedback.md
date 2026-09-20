# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No `simulate_agent.py` file or code snippet was provided showing a heuristic solver that uses the logistic function `P(retrieval) = sigmoid(α * (density - threshold))`. Likewise, there is no evidence that `α` and `threshold` are defined as configurable constants with defaults. The required implementation and configuration are missing.
- `T013` (rejected 1x): No code changes to `simulate_agent.py` are present, and there is no implementation that samples from the logistic function to set `agent_heuristic_success` nor logic handling the edge case where critical evidence occurs on the final turn. The required artifact (updated script with the specified success logic) is missing.
- `T015` (rejected 1x): No evidence of a modified `simulate_agent.py` that streams results to `data/processed/` after each batch is provided; the required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

