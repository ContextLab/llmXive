# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T039` (rejected 1x): The required markdown report `docs/reports/001-llmxive-mipu-gap-bounds_viz.md` does not exist, so the core deliverable is missing. The script file is present but its content is truncated and there is no evidence that it successfully creates the required visualizations and writes the markdown file. The next implementer must ensure the script generates the three specified plots and writes them into the missing markdown report at the correct path.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

