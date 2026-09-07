# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): The provided `scripts/recovery_reset.py` exists but the shown code does not include a main entry that checks `research.md` and exits with the required status codes, nor does it demonstrate scanning the `tests/` directory or actually modifying `tasks.md` to reset tasks T015‑T035. Without these parts, the script does not fulfill the full specification. The next implementer should add the missing execution logic, ensure the script scans `tests/`, updates `tasks.md` as described, and returns the correct exit codes.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

