# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T028` (rejected 1x): The repository contains `code/analysis/model_fitting.py`, but the required output file `data/processed/modulation_amplitudes.csv` is absent, and the visible portion of the script does not demonstrate that it computes the peak‑to‑trough difference with `max(fit) - min(fit)` nor writes those values to the CSV. The missing CSV indicates the task’s core deliverable was not produced.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

