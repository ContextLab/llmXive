# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `.gitignore` file, a `.git` directory, or any commit history is provided; the implementer’s claim cannot be verified against actual artifacts. The required repository initialization steps are not demonstrated.
- `T002a` (rejected 1x): The required file `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/requirements.txt` does not exist, even though a similarly named `code/requirements.txt` with the correct contents is present elsewhere. The task specifically demanded the file at the given project path, which is missing.
- `T002b` (rejected 1x): The required `requirements.txt` file is missing, so there is no evidence that `pip install -r requirements.txt` was run, nor any verification of a clean virtualenv installation. Without the file and installation logs, the task is not satisfied.
- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T013c` (rejected 1x): The `verify_gt.py` script is present but its implementation is truncated and never invoked to produce the required `data/raw/guava/gt_verified.json`. The expected output file is missing, so the verification step required by the task is not fulfilled.
- `T005a` (rejected 1x): The implementer did not provide any evidence (e.g., a directory listing, screenshot, or command output) showing that a `state/` directory exists in the repository root. Without such proof, we cannot confirm the required artifact is present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

