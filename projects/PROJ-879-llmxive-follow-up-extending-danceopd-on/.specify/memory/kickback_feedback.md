# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T035b` (rejected 1x): No coverage run output, pytest results, or code diff is provided to demonstrate that dead code and unused imports have been removed from the `code/` modules. Without such artifacts, we cannot verify that the requirement has been satisfied.
- `T035c` (rejected 1x): The claim provides no actual artifact (e.g., updated `code/` files, a log showing `python -m code.import` executing without ImportError, or a test script). Without concrete code changes or execution evidence, we cannot confirm that circular dependencies were removed or that the verification command runs successfully. The required artifact is missing.
- `T036a` (rejected 1x): The submission contains no code, script, or documentation showing a chunked‑loading implementation, nor any memory‑profiling data demonstrating a peak below 6 GB. Consequently the required performance‑optimization artifact and verification evidence are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

