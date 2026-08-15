# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000c` (rejected 1x): The required deliverable `research/citation_verification_log.md` is not present (or its contents are not shown), so there is no evidence that the JSON was parsed, citations were checked, or a status line was written. The task therefore remains unfinished.
- `T001b` (rejected 1x): No `research.md` file is present or shown, and there is no evidence that the literature review findings or power analysis targets have been synthesized from `validation_report.json` and `power_report.md`. The required artifact is missing, so the task is not satisfied.
- `T003` (rejected 1x): No `research.md`, `research/power_calculation.json`, or `plan.md` contents were provided, nor any validation evidence showing they meet Phase 0 requirements. The required artifacts are missing, so the task cannot be considered completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

