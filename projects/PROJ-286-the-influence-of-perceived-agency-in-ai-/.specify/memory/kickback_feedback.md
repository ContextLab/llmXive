# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No Python code, notebook, or output files showing a pre‑study power analysis for the planned directional contrasts and the overall ANOVA are present. The claim lacks any concrete artifact (e.g., a script using `scipy.stats`/`numpy`, calculated sample size or power values, or a report of the results), so the requirement is not demonstrably satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

