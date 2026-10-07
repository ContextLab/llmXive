# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T028` (rejected 1x): No updated `quickstart.md` file was provided, nor any excerpt showing the exact commands to run the full pipeline or instructions for verifying the “Limitations” text in the output report. The required documentation artifact is missing.
- `T032a` (rejected 1x): declared artifact(s) missing/empty/invalid: results/robustness_check.json
- `T033` (rejected 1x): declared artifact(s) missing/empty/invalid: results/model_residuals.png

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

