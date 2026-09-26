# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No evidence of the required `specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md` file or an updated `spec.md` that references the amendment or marks FR‑003 as “Amended” was provided. Both artifacts are missing, so the ratification task is not satisfied.
- `T002` (rejected 1x): The required file `projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/requirements.txt` does not exist, and the existing `code/requirements.txt` contains a different package list, not the specified specification excerpt. The task’s core artifact is missing.
- `T035` (rejected 1x): No code, data, or visualizations implementing the Threshold and LOIO sensitivity analyses were provided; the claim lacks any concrete artifact demonstrating that the required analysis was performed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

