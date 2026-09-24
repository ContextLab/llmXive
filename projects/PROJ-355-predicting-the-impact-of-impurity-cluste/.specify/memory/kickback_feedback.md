# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No directory structure or `.gitkeep` files were presented; without visible evidence of `data/raw/`, `data/processed/`, and `results/` containing `.gitkeep`, the requirement cannot be confirmed. The implementer must provide the actual folder hierarchy and placeholder files.
- `T009` (rejected 1x): No evidence of the required `tests/unit/` and `tests/integration/` directories (or any test files within them) was provided; without these scaffolding artifacts the task is not satisfied.
- `T018` (rejected 1x): The repository contains `code/data/descriptor_filter.py`, which implements loading descriptors and computing VIF, but it does not include any code that writes `data/processed/collinearity_report.md`. The required report file is absent, so the task of generating the VIF report (whether high collinearity or none) is not fulfilled. The next implementer must add logic to create the markdown report and ensure the file exists.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

