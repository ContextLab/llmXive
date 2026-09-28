# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): I looked for the `projects/PROJ-066-investigating-correlations-between-molec/` directory and any files inside it, but no such folder or its contents were provided. Without the actual project structure present, the task requirement is not satisfied. The implementer must add the requested directory with the appropriate subfolders and starter files.
- `T003` (rejected 1x): The implementer supplied only a feature specification for a molecular‑descriptor analysis pipeline and no artifacts related to configuring linting/formatting tools (e.g., no `pyproject.toml` with Black settings, no `.ruff.toml` or `ruff.toml`, nor any documentation or scripts invoking Black/Ruff). Consequently, the required linting configuration is missing.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): The claim only includes a feature specification and user stories; there is no evidence that the required directories (`data/raw/`, `data/processed/`, `code/data/`, `code/models/`, `code/utils/`, `tests/`) actually exist or contain any files. The task’s core deliverable – the directory structure – is missing.
- `T009` (rejected 1x): The `data/raw/chembl_33.db` file is absent, and the project state YAML still has an empty `artifacts` list (no checksum recorded). Moreover, the provided `download.py` is truncated and shows no logic that writes the checksum into `state/projects/PROJ-066-investigating-correlations-between-molec.yaml`. These missing artifacts mean the task’s core requirements are not satisfied.
- `T015` (rejected 1x): The required output file `data/processed/molecules_processed.csv` does not exist, and the schema file `contracts/molecule.schema.yaml` is also missing, so the validation step cannot be performed. Consequently the implementation cannot be verified as calling `update_state.py` or completing the write operation.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

