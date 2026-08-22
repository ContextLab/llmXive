# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree, configuration files, or README showing the required project structure were provided; the claim contains no tangible artifacts to confirm that a proper project scaffold was created. The implementer must supply the actual folder layout (e.g., `raw/`, `results/`, `scripts/`, `config/`, `pipeline.log` etc.) and any initial files that constitute the project structure.
- `T002` (rejected 1x): The implementer only supplied a feature specification and user stories; there is no repository, configuration file, or script that actually creates a Python 3.11 / R 4.3 project or declares the listed dependencies (e.g., no `pyproject.toml`, `requirements.txt`, `renv.lock`, Dockerfile, or environment setup script). Consequently the required artifact—an initialized project with the specified packages—is missing.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a `pre-commit` hook) or any documentation of their setup are present. Consequently the required artifact that demonstrates flake8 and Black have been configured for the project is missing.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logger.py
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/hash.py
- `T007` (rejected 1x): No files were found under `src/data_models/`, and there is no code defining the required classes (`RNASeqSample`, `SplicingEvent`, `EnrichmentResult`, `PhylogeneticTree`). The implementer must add non‑empty Python (or appropriate language) modules in that directory containing the base data model definitions.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

