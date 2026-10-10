# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `task-format` (rejected 1x): Tasker produced only 0 task IDs (need >= 5; total chars: 15548). Regenerate the complete tasks.md as canonical '- [ ] T### description' checkbox items, not task tables or fenced examples. Preserve every scientific requirement, path and verification step; do not add empty tasks or discard requirements to satisfy the format.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

