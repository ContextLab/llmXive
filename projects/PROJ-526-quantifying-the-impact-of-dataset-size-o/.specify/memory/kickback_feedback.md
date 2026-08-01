# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required root folders (`projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/`, `code/`, `data/`, `tests/`, `state/`, `docs/`) actually exist; without such artifacts the claim cannot be verified.
- `T001b` (rejected 1x): No directory listings or file system evidence were provided showing that the required subdirectories (`data/raw/`, `data/processed/`, `tests/contract/`, `tests/unit/`, `tests/integration/`) actually exist; without such artifacts the claim cannot be verified. The implementer must supply a view of the project tree or confirm creation of these folders.
- `T001c` (rejected 1x): No git repository was initialized and no `.gitignore` file was provided in the evidence; the required artifacts are missing, so the task of creating a repository and ignore file is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .flake8, pyproject.toml/black settings, pre‑commit hooks) are present in the provided evidence, so the requirement to “Configure linting (flake8/black) and formatting tools” is not satisfied. The implementer must add the appropriate configuration artifacts and ensure they are non‑empty.
- `T004` (rejected 1x): No evidence of a `data/` directory (with `raw/` and `processed/` subfolders) or a `state/` directory for checksums is present in the provided artifacts; the implementer’s claim cannot be verified. The required directory structure must be created and shown.
- `T035` (rejected 1x): No evidence of a `state/amendments.md` file or its contents was provided; without the actual amendment record documenting the Constitution Principle VII deviation and the N=2‑3 data availability constraint, the task requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

