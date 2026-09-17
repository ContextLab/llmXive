# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure is shown in the provided evidence; the required `projects/PROJ-312-evaluating-the-impact-of-code-generation/` folder with its subfolders (`code/`, `data/`, `tests/`, `contracts/`, `artifacts/`, `state/`) is not present or documented. The implementer must create and list these directories to satisfy the task.
- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/pyproject.toml
- `T004` (rejected 1x): No `contracts/` directory or schema definition files were provided; the required local schema definitions are missing entirely. The task’s core deliverable is absent, so the claim is not satisfied.
- `T006` (rejected 1x): No `logs/pipeline.log` file with JSON‑formatted entries is present, and there is no code shown that configures logging or records the `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers on API calls. The required logging infrastructure is therefore missing.
- `T008` (rejected 1x): No evidence was presented showing that the required directories (`data/raw/`, `data/processed/`, `data/spot_check/`, `artifacts/`, `tests/`) actually exist in the repository; the claim is unsubstantiated. The implementer must provide a directory listing or screenshots confirming the creation of these folders.
- `T011` (rejected 1x): The test file `tests/contract/test_schema_validation.py` exists and contains contract tests for `pull_request.schema.yaml`, but the required schema file `contracts/pull_request.schema.yaml` is missing, so the tests cannot actually validate anything. Add the missing `pull_request.schema.yaml` (and any other referenced schemas) with the correct structure.
- `T012b` (rejected 1x): No script, notebook, or data files were provided that fetch PRs for the repositories from T012a, iterate through each PR’s commits, and extract commit messages. The required artifact (code and/or output CSV containing the commit messages) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

