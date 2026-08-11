# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No artifact showing a `code/` directory or an `__init__.py` file was provided; the evidence list is empty, so the required files cannot be confirmed to exist. The implementer must add the `code/` folder with a non‑empty `__init__.py` inside.
- `T001b` (rejected 1x): No evidence of a `tests/` directory or its required sub‑folders (`contract/`, `unit/`, `integration/`) was provided; the implementer’s claim cannot be verified from the supplied artifacts. The missing directory structure must be added and shown.
- `T001c` (rejected 1x): No evidence of a `data/` directory or its required subfolders (`raw/`, `processed/`, `results/`, `config/`) was provided; the implementer’s claim is unsupported by any visible artifacts.
- `T002b` (rejected 1x): No `.gitignore` file or virtual environment configuration (e.g., `requirements.txt`, `pyproject.toml`, or `venv/` setup script) was presented. Without these artifacts, the claim that the task “Create `.gitignore` and initialize virtualenv configuration” is fulfilled cannot be verified. The next implementer must add a proper `.gitignore` file and provide the necessary virtual environment setup files.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

