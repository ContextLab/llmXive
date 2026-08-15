# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T033a` (rejected 1x): No `research.md` file or excerpt was provided, and there is no evidence that the methodological shift from ANOVA to a permutation test has been documented, justified, or cited as required. The implementer must supply a non‑empty `research.md` containing the explanation and citation.
- `T027b` (rejected 1x): No evidence of a `logs/counterbalance_strategy.log` file was provided; the claim lacks any artifact showing the log’s existence, content, or the specific counterbalancing strategy recorded. The required log file must be present and contain the strategy details for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

