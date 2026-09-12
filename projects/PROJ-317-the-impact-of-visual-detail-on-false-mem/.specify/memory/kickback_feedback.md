# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The provided `metadata.py` does not use `datetime.now(timezone.utc)`, never reads `data/assets/generation_log.json` (the file is missing), and contains no logic to write the required `data/stimuli/{id}_metadata.yaml` files or include the asset parameters. Additionally, the script is truncated (e.g., `return` statement is incomplete) and no generated metadata files are present. These omissions mean the task requirements are not met.
- `T035#1` (rejected 1x): The repository contains `code/analysis/anova.py`, but the file is truncated and never writes the required `data/analysis/anova_results.json`. Moreover, the JSON results file is missing entirely, so the task’s output artifact and schema verification are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

