# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T022a` (rejected 1x): declared artifact(s) missing/empty/invalid: docs/agent_list.md
- `T009b` (rejected 1x): declared artifact(s) missing/empty/invalid: assets/templates/verified_template_url.txt, assets/templates/TEMPLATE-001-v1.0.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

