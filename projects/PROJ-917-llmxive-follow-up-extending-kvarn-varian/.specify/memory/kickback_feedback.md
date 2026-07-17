# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `code/` directory or the required sub‑directories (`data_generation`, `model_training`, `simulation`, `analysis`, `tests/`) is provided; the claim lacks any file or folder listings to confirm the structure exists. The task remains undone until the directory hierarchy is created and shown.
- `T001b` (rejected 1x): No evidence of a `data/` directory or its required subfolders (`generated`, `models`, `simulation`, `analysis`) is presented; the implementer provided only narrative text without any filesystem artifacts to confirm the structure exists. The task therefore remains unfulfilled.
- `T001c` (rejected 1x): The provided information contains no evidence of a `tests/` directory or the required sub‑directories (`test_data_generation`, `test_model_training`, `test_simulation`). Without these artifacts present, the task requirement is not satisfied. The next implementer should create the `tests/` folder with the three specified subfolders and include appropriate test files.
- `T003` (rejected 1x): The provided artifacts relate to synthetic data generation, model training, and simulation for the KVarN project, with no configuration files, scripts, or documentation for ruff linting or black formatting. No `.ruff.toml`, `pyproject.toml` (or equivalent) or CI setup for these tools is present, so the linting/formatting task is not satisfied.
- `T004` (rejected 1x): The submission provides no `data/` directory, no file hierarchy, and no implementation of checksumming logic for immutable raw data; there is no code, script, or documentation evidence of such setup. Consequently the core requirement of task T004 is missing.
- `T006` (rejected 1x): No code, data, or documentation for a simulation state tracking framework (cumulative error state or KL‑divergence accumulator) is present; the only artifacts described relate to data generation, model training, and simulation runs, not to the required tracking infrastructure. The task’s core deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

