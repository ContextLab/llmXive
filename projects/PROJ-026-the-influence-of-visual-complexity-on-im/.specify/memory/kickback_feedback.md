# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listing was provided to confirm that the required folders (`code/data`, `code/stimuli`, `code/analysis`, `code/viz`, `code/tests`, `data/raw/stimuli`, `data/raw/responses`, `data/processed`, `data/results`) actually exist. The implementer must supply evidence (e.g., `tree` output or a screenshot) showing the exact structure.
- `T036` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/permutation_results.json, data/results/sensitivity_results.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

