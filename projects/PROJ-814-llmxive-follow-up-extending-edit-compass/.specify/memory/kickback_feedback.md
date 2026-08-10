# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001h` (rejected 1x): The implementer supplied only a high‑level feature specification and no concrete artifact showing a `data/raw` directory was created (or even listed). There is no evidence on disk of the required folder, so the task’s simple requirement is unmet.
- `T001i` (rejected 1x): No evidence of a `data/filtered` directory (or its contents) was presented; without a visible directory or confirmation that it was created, the requirement is not satisfied. The implementer must provide the actual directory (and preferably the filtered files) as proof.
- `T001j` (rejected 1x): No evidence of a `data/scores` directory was presented; the artifact list is empty, so we cannot confirm that the required directory was created. The implementer must add the directory (and optionally show its presence) to satisfy the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

