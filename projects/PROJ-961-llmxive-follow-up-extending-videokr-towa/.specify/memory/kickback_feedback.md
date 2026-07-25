# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `code/`, `tests/`, or `data/` directories is provided; the claim lacks any listed files or directory listings confirming their existence or non‑emptiness. The implementer must create these three top‑level folders and populate them with at least placeholder content to satisfy the task.
- `T001b` (rejected 1x): No evidence of the required `code/ingest/`, `code/analysis/`, or `code/utils/` directories is provided; the claim lacks any artifact showing that these subdirectories exist. The implementer must create and show these directories (e.g., a directory listing or file paths) to satisfy the task.
- `T001c` (rejected 1x): No evidence was presented showing that the `tests/unit/` and `tests/integration/` directories actually exist in the repository (e.g., a directory listing, file paths, or any files within them). Without such artifacts, we cannot confirm the required subdirectories were created.
- `T008a` (rejected 1x): No `.gitkeep` file in `data/raw/` was shown or described; the implementer provided no artifact or proof that the file exists, so the requirement is not demonstrated.
- `T008b` (rejected 1x): No evidence of a `.gitkeep` file in the `data/processed/` directory was provided; the implementer did not supply the required file or any proof of its existence. The task remains undone until the placeholder file is created and shown.
- `T028b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/stability_metric.json
- `T031b` (rejected 1x): No code files from the `code/` directory were presented, nor any diff, type‑hinted signatures, or a report confirming that every public function now includes type annotations. Without concrete artifacts showing the added type hints, the requirement cannot be verified as satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

