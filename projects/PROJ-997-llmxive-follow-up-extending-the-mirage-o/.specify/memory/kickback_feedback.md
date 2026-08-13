# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or `__init__.py` files were presented as evidence, so we cannot confirm that the required `src/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/`, `docs/reports/`, `src/lib/`, `src/services/`, `src/cli/`, `src/config/`, `src/models/` directories (and their `__init__.py` files) actually exist. The implementer must provide the filesystem layout or a listing showing these directories and files.
- `T003` (rejected 1x): The `pyproject.toml` correctly contains a `[tool.black]` section, but the required `.ruff.toml` file is absent, so the linting configuration is incomplete. The missing `.ruff.toml` must be added with the appropriate Ruff settings.
- `T004` (rejected 1x): No evidence was provided that the directories `data/raw/`, `data/processed/`, and `data/models/` actually exist in the repository; the response contains only the task description and specifications, with no file‑system listing or screenshots showing the required folder structure. The implementer must create and commit these three directories (non‑empty) to satisfy the task.
- `T015` (rejected 1x): The `src/cli/generate_dataset.py` file exists, but the provided excerpt is truncated and does not demonstrate that it streams GSM8K/Ultrachat prompts, runs the paired feature‑extraction and quantized‑inference loop, and writes the required Parquet file. Moreover, the expected output `data/processed/training_sample.parquet` is absent from the repository. The task’s core deliverable is therefore not present.
- `T017` (rejected 1x): No code, configuration, or log output files were provided that demonstrate logging of data‑generation progress, skipped samples, or quantization errors. The claim lacks any concrete artifact (e.g., updated scripts, log examples, or documentation) showing the required logging has been added.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

