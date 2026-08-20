# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005c` (rejected 1x): The provided `code/verify_manifest.py` is present, but the shown implementation does not demonstrate handling of an empty manifest (logging a warning and recording a `'MISSING_DATA'` status) and writes the hash under the key `data_raw_manifest` rather than under `artifact_hashes` for `data/raw` as required. Moreover, the state file `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` lacks any entry for the manifest checksum, indicating the script has not recorded the hash correctly. The task’s core requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

