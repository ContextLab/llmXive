# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The test file `tests/contract/test_schemas.py` is present, but the required schema `contracts/task.schema.yaml` (and likely `contracts/skill.schema.yaml`) does not exist, causing the test to fail. Additionally, there is no evidence that `data/raw/tasks.json` (or `skills.json`) is present and populated. The missing schema (and data) files must be added for the contract test to be functional.
- `T012` (rejected 1x): The provided `tests/contract/test_schemas.py` references `contracts/skill.schema.yaml`, but that schema file is missing, so the test cannot run. Moreover, the test only validates the JSON schema and does not check any “overlap metrics” as required by the task. The missing schema file and lack of overlap‑metric validation must be added for the task to be considered complete.
- `T015` (rejected 1x): The repository lacks the required output files `data/raw/skills.json` and `data/raw/tasks.json`; they are missing entirely. The existing `data/raw/checksums.json` contains placeholder strings rather than real SHA‑256 hashes, and there is no evidence that `state/artifact_hashes.json` was updated. Additionally, the provided `code/generate_data.py` is truncated and does not contain the full serialization or checksum logic. The task’s requirements are therefore not satisfied.
- `T016` (rejected 1x): The required `data/raw/tasks.json` file does not exist, so the flag cannot be set, and the shown portion of `code/generate_data.py` contains no logic for detecting mean pairwise similarity, setting `maximal_overlap_detected`, or handling deterministic tie‑breaking as specified. The task’s core requirements are therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

