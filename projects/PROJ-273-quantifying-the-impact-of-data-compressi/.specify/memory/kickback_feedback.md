# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): declared artifact(s) missing/empty/invalid: code/provenance/deviation_constitution_principle_ii.md, state/projects/PROJ-273-quantifying-the-impact-of-data-compressi.yaml
- `T006` (rejected 1x): No evidence was provided that the required directories (`data/raw/`, `data/interim/`, `data/processed/`, `data/external/`) actually exist; the response contains no file listings, screenshots, or code creating them. The implementer must add the directory structure to the repository (or provide proof of its presence).
- `T015` (rejected 1x): No code, script, or output files were provided that demonstrate a loop fetching additional noise segments in batches, validating them, and ensuring ≥12 valid events with complete spin metadata. Without such artifacts, the requirement cannot be verified. The implementer must supply the actual implementation (e.g., a function or module) and evidence (logs, test results, or data files) showing the batch‑fetching and validation logic works as specified.
- `T016` (rejected 1x): No updated description of T015 is present in the provided evidence; the claim that the specification now clarifies stopping after 12 valid events cannot be verified because the artifact itself is missing. The next implementer must supply the revised T015 text showing the required clarification.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or scripts setting up ruff linting and black formatting are present; the only artifacts shown relate to a data‑compression feature, not to linting/formatting setup. Consequently the required linting/formatting configuration is missing.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/inject.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

