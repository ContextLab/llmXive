# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that a `code/scripts/` directory actually exists in the repository (e.g., a directory listing, screenshot, or commit diff). Without such proof, we cannot confirm the required artifact was created.
- `T001b` (rejected 1x): No evidence was provided showing that the directory `code/data/raw/` actually exists (or was created). The implementer’s claim lacks any artifact (e.g., a directory listing or screenshot) to verify the required folder was made. The missing proof must be supplied for the task to be considered complete.
- `T001c` (rejected 1x): No evidence was provided that the directory `code/data/processed/` actually exists; the artifacts shown relate only to higher‑level user stories and contain no filesystem listing or created folder. The required directory creation step is missing.
- `T001d` (rejected 1x): No evidence was presented showing that a `code/data/splits/` directory exists in the repository (or that it contains any files). Without a visible directory or confirmation of its creation, the task requirement is not satisfied. The implementer must add the directory (and optionally populate it) and provide proof (e.g., a directory listing).
- `T001e` (rejected 1x): No evidence of a `code/models/` directory was provided; the artifact list is empty, so the required directory does not appear to exist. The implementer must create the directory (and optionally add a placeholder file) to satisfy task T001e.
- `T001f` (rejected 1x): No evidence was provided showing that a `code/tests/` directory exists in the repository (e.g., a directory listing or file within it). Without such proof, we cannot confirm the required artifact was created. The implementer must add a visible confirmation that the directory now exists (e.g., a screenshot of the repo tree, a commit diff, or a placeholder test file inside the folder).

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

