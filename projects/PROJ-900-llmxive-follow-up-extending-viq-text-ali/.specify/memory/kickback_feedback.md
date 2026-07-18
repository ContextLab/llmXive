# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `data/raw/`, `data/processed/`, `data/results/`, `code/`, or `tests/` directories (each containing a `.gitkeep` file) was provided; the claim lacks any artifact showing these folders exist. The implementer must add the directories with non‑empty `.gitkeep` placeholder files.
- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/requirements.txt
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` entries for ruff/black, `.ruff.toml`, or CI scripts invoking these tools) were provided, nor any evidence that the tools have been set up and run. The required artifacts are missing, so the task is not satisfied.
- `T014` (rejected 1x): The repository does not contain the expected checkpoint file `data/results/codebook_v0.pth`, and the provided excerpt of `code/train.py` shows no logic for saving a model checkpoint to that path. The required artifact is missing, so the task is not fulfilled.
- `T016` (rejected 1x): No code, configuration, or log output was presented showing that training loss, reconstruction loss, and codebook usage statistics are now being logged. The required artifact (e.g., updated training script with logging statements or sample log files) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

