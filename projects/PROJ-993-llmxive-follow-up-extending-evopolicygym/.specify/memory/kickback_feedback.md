# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/discovered_envs.log, data/discovered_envs.json
- `T015b` (rejected 1x): No schema definition file (e.g., CSV header list, JSON schema, or code comment) was provided; the evidence contains only the task description without any concrete artifact specifying the required columns and types. The implementer must supply a tangible schema definition for `sensitivity_report.csv`.
- `T013e` (rejected 1x): declared artifact(s) missing/empty/invalid: data/discovered_envs.json
- `T013f` (rejected 1x): declared artifact(s) missing/empty/invalid: data/discovered_envs.json, data/sensitivity_report.csv
- `T023` (rejected 1x): The provided `generator.py` includes a `handle_fallback` that logs to `data/fallbacks.log` and returns a `TemplateExplanation` object, satisfying the logging and object‑return parts. However, the implementation never returns a scalar reward signal as an alternative fallback, nor is there any code showing such a path. Consequently the requirement “return a `TemplateExplanation` object **OR a scalar_reward signal**” is not met. The missing scalar‑reward fallback must be added for the task to be complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

