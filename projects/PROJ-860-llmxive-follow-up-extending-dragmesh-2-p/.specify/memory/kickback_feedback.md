# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory tree or list of created folders (`code`, `tests`, `data/raw`, `data/generated`, `state/projects`, `data/results`) is provided; without concrete evidence the required repository layout has not been demonstrated.
- `T001c` (rejected 1x): The script `checksum_config.py` checks for the existence of `requirements.txt` and `pytest.ini`, but both files are missing, so the script would abort and never write real hashes. The YAML file present contains hash values for those non‑existent files, indicating they are fabricated placeholders rather than genuine SHA256 checksums. The required artifacts are therefore not correctly generated.
- `T002` (rejected 1x): The required file `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/requirements.txt` does not exist, so no pinned dependencies are present at the specified location. The existing `code/requirements.txt` is at a different path and does not fulfill the task.
- `T003` (rejected 1x): The required file `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/pytest.ini` is missing, and the provided `code/pytest.ini` does not configure a separate 6‑hour timeout for integration tests (it only sets a global 3600‑second timeout). The task therefore remains unfulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

