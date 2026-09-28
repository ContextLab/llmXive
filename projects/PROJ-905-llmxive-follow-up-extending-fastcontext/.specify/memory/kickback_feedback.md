# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or other evidence was provided showing that `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` contains the required subfolders (`data/raw`, `data/processed`, `data/results`, `code`, `tests/unit`, `tests/integration`, `specs/contracts`, `state`). Without this concrete artifact, the task requirement is not verified.
- `T002` (rejected 1x): The required file `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` does not exist, so the project was not initialized at the specified location. The existing `requirements.txt` files are in the wrong directories.
- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T003b` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml
- `T007b` (rejected 1x): The required CSV file `data/raw/ground_truth_annotations.csv` does not exist, and the provided `annotation_extractor.py` is incomplete (truncated) and extracts a `ground_truth` field rather than the specified `ground_truth_files`, with no evidence that it writes the required columns in the correct JSON‑encoded format. The task’s output artifact is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

