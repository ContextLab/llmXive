# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024` (rejected 1x): The `prepare_sensitivity_thresholds` function is implemented correctly and can write the required JSON, but the repository lacks the `data/processed/thresholds.json` file and the `code/main.py` script is truncated (missing the CLI subcommand definition for `prepare‑thresholds`). Without a complete command implementation and the generated output file, the task’s full requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

