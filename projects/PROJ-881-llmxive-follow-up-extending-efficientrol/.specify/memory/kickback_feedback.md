# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): The required file `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` does not exist, so the deliverable is missing despite a similar `code/requirements.txt` being present elsewhere. The task is therefore not satisfied.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml, black.toml
- `T010` (rejected 1x): The provided `download.py` only implements streaming download and 500‑example capping for GSM8K; there is no analogous logic for the MiniGrid dataset, and the file is located at `code/src/data/download.py` rather than the required `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py`. Both the missing MiniGrid implementation and the incorrect file location prevent the task from being satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

