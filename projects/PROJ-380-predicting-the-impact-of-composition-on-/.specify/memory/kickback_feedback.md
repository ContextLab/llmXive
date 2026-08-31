# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`code/`, `data/`, `tests/`, `docs/`) is provided; the claim lacks any artifact showing that the structure was created. The implementer must add the missing folder hierarchy (and optionally placeholder files) to satisfy the task.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or integration scripts are present; therefore the required artifact for configuring ruff/flake8 and Black does not exist.
- `T005` (rejected 1x): No `utils/config.py` file or its contents were presented, so there is no evidence that random seeds and path constants have been defined as required. The implementer must add the file with appropriate seed initializations and path constant definitions.
- `T006` (rejected 1x): No `utils/provenance.py` file is present, nor any code showing checksum generation or recording to the required `state/projects/PROJ-380-...yaml` file. The evidence provided consists only of a project description, so the required implementation is missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): No evidence was provided that a `data/` directory (with subfolders `raw/`, `processed/`, and `artifacts/`) actually exists in the repository; the claim is unsupported by any listed files or screenshots. The required directory structure must be created and shown (e.g., via a directory tree listing).
- `T012a` (rejected 1x): No `utils/provenance.py` file or any code implementing checksum recording logic is present in the provided artifacts; the only evidence relates to a shear‑modulus prediction pipeline, which does not address the required provenance checksum feature. The missing implementation must be added to `utils/provenance.py`.
- `T011` (rejected 1x): The provided `synthetic_generator.py` is truncated, lacks any reference to `research.md`, and contains no logic to write the generated data to `data/raw/synthetic_bmg_seed.csv`. Moreover, the required CSV file does not exist. These missing pieces mean the task’s core requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

