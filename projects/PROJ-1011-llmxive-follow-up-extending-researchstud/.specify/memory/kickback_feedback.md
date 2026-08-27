# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that `projects/PROJ-1011-llmxive-follow-up-extending-researchstud/`, `code/`, `data/`, `tests/`, and `state/` actually exist; the implementer supplied no artifacts to confirm the required structure was created.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook) or setup scripts are present in the provided evidence, so the requirement to configure ruff and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are integrated into the project (e.g., via `pre-commit` or CI).
- `T004` (rejected 1x): No directory structure (`data/raw`, `data/processed`, `data/results`) or checksum manifest code/file is presented; the response contains only the task description and specifications, without any concrete artifacts to verify the setup. The required files and logic are missing.
- `T007` (rejected 1x): No files or code snippets for `code/models/Abstract.py`, `PatternCard.py`, `Proposal.py`, or `Rating.py` were presented, and the directory `code/models/` was not shown to contain the required model definitions. The task therefore lacks the essential artifacts.
- `T008` (rejected 1x): No code, configuration, or documentation was provided that implements an error‑handling layer which “fails loudly” on data‑fetch failures. The claim lacks any artifact (e.g., a Python module, try/except wrappers, logging setup, or test demonstrating the loud failure), so the requirement is not satisfied.
- `T008b` (rejected 1x): No logging infrastructure code, configuration, or documentation was provided; the claim contains only a textual description of the overall project and user stories, with no artifact that records model switches or memory fallback events. The required logging implementation is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

