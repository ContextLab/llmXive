# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- `T005` (rejected 1x): The CLI script exists and exits 0, producing a schema‑valid `data/results/smoke_report.json`, but there is no provided evidence that `logs/pipeline.jsonl` was created and contains the required `"cli_start"` event (the file’s content is not shown). Without confirming this log entry, the task’s verification criteria are not fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

