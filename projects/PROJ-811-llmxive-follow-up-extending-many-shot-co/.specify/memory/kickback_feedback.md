# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T026` (rejected 1x): No batch‑runner script or generated prompt files are present in `data/processed/prompts/`; the claim provides no code, configuration, or output artifacts to demonstrate that prompts for multiple seeds and three strategies were actually created. The required files must be added and verified.
- `T027` (rejected 1x): The claim provides only a high‑level description of the feature and no concrete artifact (e.g., source code changes, unit tests, or documentation) that implements or verifies the “no duplicate orderings within a strategy group across seeds” validation. Without any code, test suite, or evidence of the validation logic, the requirement is not satisfied. The next implementer must add the actual validation implementation (e.g., in the ordering generation module) and include tests demonstrating that duplicate orderings are detected and prevented across different random seeds.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

