# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/`, `data/`, `data/raw_cif/`, `models/`, `results/`, `contracts/`, `specs/`) actually exist; the response contains only the task description and specifications, not the concrete project structure. The implementer must create and show the directory hierarchy (e.g., via a tree listing or screenshots) to satisfy the requirement.
- `T003` (rejected 1x): No `.gitignore` file content or path was provided in the evidence, so we cannot confirm that a file exists, is non‑empty, and contains the required patterns (`data/raw_cif/`, `*.pt`, `*.csv`, `__pycache__`, `.env`). The implementer must supply the actual `.gitignore` file with those entries.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

