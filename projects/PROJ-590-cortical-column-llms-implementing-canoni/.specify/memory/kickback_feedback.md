# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T031` (rejected 1x): The repository contains the test script, but it is truncated and contains a syntax error (`me` instead of `mean_norm`). Moreover, the required input file `data/logs/gradient_norms.json` and the expected output file `data/results/gradient_stability_baseline.json` are absent. Without a runnable test and the necessary data files, the task’s requirements are not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

