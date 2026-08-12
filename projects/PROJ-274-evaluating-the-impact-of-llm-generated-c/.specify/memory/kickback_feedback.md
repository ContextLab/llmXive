# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021c` (rejected 1x): The repository lacks the required `data/raw/repo_covariates.json` file, and the provided `code/validation.py` excerpt shows only LOC and cyclomatic complexity calculations without any logic that writes collected metrics to that JSON path. Consequently, the task’s core deliverable—metric collection for covariate adjustment saved to `repo_covariates.json`—is not present.
- `T016` (rejected 1x): No code, data file, or JSON output was presented. The required artifact—a JSON file containing the raw help‑request logs (timestamp and content) and the computed composite “Cognitive Load Proxy” score—is missing, so the task’s functional requirements have not been demonstrated.
- `T020` (rejected 1x): The required `data/raw/participant_logs.json` file does not exist, and the `update_checksums` function in `code/data_collection.py` is incomplete (truncated) and never called after saving logs, so checksum generation is not actually implemented. The task’s export and checksum requirements are therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

