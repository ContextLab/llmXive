# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directory `projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso/` or its subfolders (`code/`, `data/`, `tests/`, `state/`) was provided; without a directory listing or files, we cannot confirm the artifact exists. The implementer must supply proof (e.g., a file tree screenshot or `ls` output) showing the created project root and subdirectories.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

