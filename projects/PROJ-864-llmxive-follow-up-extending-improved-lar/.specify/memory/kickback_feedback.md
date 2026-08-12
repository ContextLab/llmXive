# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No evidence of a `main.py` file at `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/` was provided; the claim lacks any artifact showing the file’s existence or contents. The required initialization script is therefore missing.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or similar) were presented for the `projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/` directory, so the required artifact is missing. The implementer must add the appropriate ruff and black configuration files (and optionally integrate them into CI or pre‑commit) to satisfy the task.
- `T005` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/artifacts/`) being created or listed is provided; the claim lacks any tangible artifact confirming the directory structure exists.
- `T013` (rejected 1x): No `download_micro_corpus.py` file (or its contents) was provided in the evidence, and there is no indication that the script was created or contains the required `datasets.load_dataset(..., streaming=True)` logic. The required artifact is missing, so the task is not satisfied.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/micro_corpus_full.jsonl

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

