# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/`, `code/data/`, `code/models/`, `code/eval/`, `code/utils/`, `tests/contract/`, `tests/unit/`, `tests/integration/`, `results/reports/`, `results/plots/`, `results/baseline/`, `results/predictions/`, `logs/`) actually exist. The implementer’s claim cannot be verified without concrete artifacts.
- `T001b` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/splits/`, `data/schemas/`) being created is provided; the claim lacks any artifact or file‑system listing to confirm their existence. The implementer must supply proof (e.g., a directory tree screenshot or script output) that these four directories have been created and are non‑empty.
- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T032a` (rejected 1x): No `README.md` file or its contents were provided; therefore the required overview, installation instructions, usage examples, and traceability of FR-001 to FR-007 cannot be verified. The task remains undone.
- `T032b` (rejected 1x): No `docs/` directory or documentation files were provided, and there is no evidence that API docs for `code/data/`, `code/models/`, or `code/eval/` covering FR‑001 to FR‑007 were created. The required documentation artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

