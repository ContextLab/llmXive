# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T081` (rejected 1x): The repository contains `code/data/verify_invariants.py`, but the provided excerpt is truncated and does not show any logic that actually writes the required `docs/reproducibility/computed_invariant_verification.md`. Moreover, the markdown report file is missing entirely. The task’s core deliverable – a generated verification report – is therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

