# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No `research.md` file (or its contents) was provided in the evidence, so we cannot confirm that the required document exists, is non‑empty, or contains the filtered Technical Context and correct Summary as specified. The implementer must supply the actual `projects/PROJ-487-the-impact-of-social-media-doomscrolling/specs/001-news-volume-anxiety/research.md` file with the appropriate content.
- `T004a` (rejected 1x): No evidence of a `venv` directory or any activation scripts/files was provided in the artifacts; the implementer did not supply proof that `python -m venv venv` was executed in the specified project path. The required virtual environment is missing.
- `T004b` (rejected 1x): No evidence was provided showing a `venv` directory with a `bin/activate` script, nor any check that the file is executable. The required artifact (the virtual environment activation script) is missing, so the task’s requirement is not satisfied.
- `T011` (rejected 1x): No evidence of a `test_fetch_google_trends.py` file in the specified `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/` directory was provided, nor any content showing the required mock‑based test that checks for a `ValueError` on an invalid keyword. The required test artifact is missing.
- `T014` (rejected 1x): No `test_fetch_error_handling.py` file was presented in the specified directory, nor any code showing the required mocking of 500 errors, the `test_500_exit_code` implementation, or evidence that the test was run. The essential artifact is missing.
- `T015a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/gdelt_events.csv, data/raw/google_trends.csv, state/projects/PROJ-487-the-impact-of-social-media-doomscrolling.yaml
- `T007b` (rejected 1x): The file `code/contracts/output.schema.yaml` exists and is non‑empty, but the task demanded the **exact** content of that schema, which is not provided in the prompt for comparison. Without the reference content we cannot confirm the file matches the required specification, so the requirement is not demonstrably satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

