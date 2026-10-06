# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure or any file listing was provided as evidence; the claim that the required data directories exist and contain appropriate content cannot be verified. The implementer must supply a concrete view (e.g., a tree listing or screenshots) showing the presence of `data/raw/`, `data/derived/`, `data/derived/topology/`, `data/derived/vdos/`, `data/derived/reference/`, `data/derived/correlation/`, and `data/metadata/`.
- `T001b` (rejected 1x): No evidence of the required directories (`outputs/`, `outputs/figures/`, `outputs/reports/`) being created, listed, or described is present; the implementer provided no artifact or documentation confirming the design. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

