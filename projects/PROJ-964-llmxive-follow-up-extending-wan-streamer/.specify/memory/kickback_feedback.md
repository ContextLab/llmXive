# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No directory listings or proof that the required `code/`, `code/data/`, `code/models/`, `code/inference/`, `code/evaluation/`, `code/utils/`, `code/tasks/`, and `code/tests/` folders actually exist were provided; without such evidence the `os.path.isdir` checks cannot be satisfied.
- `T003` (rejected 1x): No evidence was provided that the directories `data/raw/`, `data/processed/`, and `data/models/` actually exist; there is no script or output showing `os.path.isdir` checks passing. The required subdirectories must be created and verified.
- `T004` (rejected 1x): No evidence was presented showing that `state/` and `docs/` directories actually exist; there are no file listings, screenshots, or code confirming `os.path.isdir` returns True for those paths. The implementer must create the directories and provide proof (e.g., a directory tree listing or a test script that asserts their existence).
- `T005` (rejected 1x): No evidence was provided that the `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/` directory actually exists (e.g., a screenshot, `os.path.exists` output, or a file listing). Without such proof, the required artifact cannot be confirmed.
- `T005c` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T018` (rejected 1x): The `gru_estimator.py` file defines a GRU model that outputs a `[batch, 2]` tensor, but the script does not contain any code that saves a checkpoint to `data/models/estimator_checkpoint.pt` with a `pending_validation` flag, and the expected checkpoint file is absent from the repository. Consequently the core requirement of persisting a pending‑validation checkpoint is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

