# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or file tree was provided showing the required folders under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`. Without concrete evidence that the specified directories (`data/raw`, `data/curated`, `data/eval`, `src/generation`, `src/filtering`, `src/training`, `src/evaluation`, `src/utils`, `tests/unit`, `tests/integration`) exist, the task cannot be considered completed. The implementer must supply a verified file‑system snapshot or `tree` output confirming the full project structure.
- `T002` (rejected 1x): The implementer only supplied a feature specification and user‑story text; there is no evidence of a Python 3.11 project being created (e.g., no repository, no `pyproject.toml`/`requirements.txt`, no `setup.cfg`, no virtual‑env configuration) that includes the listed CPU‑only packages. Consequently the core requirement—initializing a project with those dependencies—is missing.
- `T003` (rejected 1x): The implementer supplied only a high‑level feature specification for a physics‑filter pipeline; no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`), setup scripts, or documentation were provided. Consequently, the required artifacts to demonstrate that ruff and black are configured for the project are missing.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/io_utils.py
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logging.py
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/training/config.py
- `T007b` (rejected 1x): declared artifact(s) missing/empty/invalid: config.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/verify_env.py
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/seeding.py
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/profile_memory.py
- `T011` (rejected 1x): No actual test artifacts (e.g., scripts, logs, output files, or result summaries) were provided; only the task description and acceptance criteria are present, so the integration test has not been demonstrated.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/generation/prompts.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

