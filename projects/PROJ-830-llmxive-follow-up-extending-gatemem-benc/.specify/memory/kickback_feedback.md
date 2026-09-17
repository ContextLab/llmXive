# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/stats.py
- `T008b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/stats.py
- `T015b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/gatekeeper/rules.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/gatekeeper/metrics.py
- `T020` (rejected 1x): No code, configuration, or test artifacts showing the added validation‑error logging, exclusion logic, or model‑load retry handling are present. The implementer provided no files or diff that demonstrate the required error‑handling changes, so the task’s requirement cannot be verified as satisfied.
- `T012` (rejected 1x): The required artifact `data/processed/access_control_results.json` does not exist, and the schema file `results.schema.yaml` (or `schema.yaml`) is also missing, so there is no content to verify against the schema. Without these files, the contract test cannot be performed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

