# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required root project directory `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/` is provided; the implementer did not show that the folder exists or contains any files. The task remains undone.
- `T002` (rejected 1x): No evidence of the required directory `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/` being present (or containing any files) is provided. The task’s sole requirement is to create that source folder, which is not demonstrated.
- `T003` (rejected 1x): No evidence of the required `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/` directory (or any files within it) is provided; without a visible, non‑empty test directory the task is not satisfied.
- `T004` (rejected 1x): No evidence of the required `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/data/` directory (or any files within it) was provided; without a visible, non‑empty directory the task is not satisfied. The implementer must create the specified data folder and show its presence.
- `T005` (rejected 1x): No evidence of the required `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/` directory (or any files within it) is provided; the response contains only the task description and no actual artifact confirming the directory was created. The implementer must supply proof that the directory exists and is non‑empty.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

