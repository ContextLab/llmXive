# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file system snapshots were provided, so there is no evidence that any of the required folders (`code/`, `data/`, `data/raw/`, `data/intermediate/`, `data/processed/`, `data/provenance/`, `data/results/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`) actually exist. The implementer must supply a view of the project tree or confirmation that these directories have been created and are non‑empty.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .flake8, pyproject.toml, setup.cfg, or similar) were presented for the `code/` directory, so there is no evidence that flake8 and black have been set up. The required artifacts are missing.
- `T004` (rejected 1x): No git‑hook files, configuration, or documentation were provided; the claim contains no artifact showing a pre‑commit hook that checks seeds or imports. The required setup for Git hooks is missing entirely.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/intermediate/merged.csv
- `T020` (rejected 1x): The required file `state/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml` does not exist in the repository, so no artifact hashes could have been added. The task cannot be considered completed until this YAML file is present and updated with the appropriate hashes.
- `T031` (rejected 1x): declared artifact(s) missing/empty/invalid: data/intermediate/merged.csv
- `T032` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/output.json, schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

