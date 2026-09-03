# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014b` (rejected 1x): The evidence contains only the task description and project specifications; there is no Python wrapper script, no parsing logic, and no output files (e.g., a generated CSV or logs) provided. Consequently, the required artifact—the implemented Python wrapper for PMD CLI integration—is missing.
- `T025` (rejected 1x): I examined the repository for any script, module, or documentation that detects projects with zero buggy files, logs a warning, and skips them gracefully as required by T025 [US2]. No such code, configuration, or output logs were present; the only artifacts relate to metric extraction and correlation analysis. The task’s specific handling of class‑imbalance is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

