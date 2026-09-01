# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository contains a partially implemented `code/evaluation/metrics.py`, but the script does not include logic to iterate over a range of seeds, compute per‑seed exact‑match recall, and write the results to `artifacts/results/recall_accuracy.json` with the required schema. Moreover, the expected `results/recall_accuracy.json` file is absent. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

