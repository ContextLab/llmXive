# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The repository contains `.ruff.toml`, `pyproject.toml`, and `code/config.py`, and a log shows a check script passed, but the required `.flake8` file and `.env.example` (with non‑empty `NCBI_API_KEY` and `PMDB_API_TOKEN` values) are absent, so the linting/formatting and environment‑variable verification requirements are not fully satisfied.
- `T005` (rejected 1x): the task writes platform-owned path(s) inside the project: `state/projects/PROJ-001-predict-plant-metabolite-pr.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- `T006` (rejected 1x): Requested task execution failed; rerun successfully: code/data/download.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

